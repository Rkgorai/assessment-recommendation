import scrapy
import re
import json
import os

class SHLCatalogSpider(scrapy.Spider):
    name = "shl_catalog"
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 0.25,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'LOG_LEVEL': 'INFO'
    }

    TYPE_MAPPING = {
        'A': 'Ability & Aptitude',
        'B': 'Biodata & Situational Judgement',
        'C': 'Competencies',
        'D': 'Development & 360',
        'E': 'Assessment Exercises',
        'K': 'Knowledge & Skills',
        'P': 'Personality & Behavior',
        'S': 'Simulations'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch = []
        self.file_path = 'data/raw_catalog.jsonl'
        
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        open(self.file_path, 'w', encoding='utf-8').close()

    def start_requests(self):
        self.logger.info("🚀 STARTING TYPE 1 PROCESSING...")
        start_url = "https://www.shl.com/products/product-catalog/?start=0&type=1"
        yield scrapy.Request(
            url=start_url, 
            callback=self.parse, 
            meta={'start_index': 0, 'type_id': 1},
            dont_filter=True
        )

    def parse(self, response):
        type_id = response.meta['type_id']
        start_index = response.meta['start_index']
        
        # --- EXPLICIT HARD STOP FOR TYPE 2 ---
        if type_id == 2:
            self.logger.info("🛑 Reached Type 2. Breaking, flushing remaining data, and ending process.")
            self.flush_batch()
            return

        # --- STRICT HEADING FILTER ---
        # Only extract from the table if it explicitly contains the "Individual Test Solutions" heading
        target_table = response.xpath('//table[.//th[contains(text(), "Individual Test Solutions")]]')
        
        if not target_table:
            self.logger.warning(f"⚠️ Could not find 'Individual Test Solutions' table on {response.url}. Breaking.")
            self.flush_batch()
            return
            
        rows = target_table.xpath('.//tr[@data-course-id or @data-entity-id]')
        
        for row in rows:
            link = row.css('td.custom__table-heading__title a::attr(href)').get()
            
            if not link:
                continue
            
            absolute_link = f"https://www.shl.com{link}"
            tds = row.css('td')
            
            remote_support = "Yes" if tds[1].css('.catalogue__circle.-yes') else "No"
            adaptive_support = "Yes" if tds[2].css('.catalogue__circle.-yes') else "No"
            
            keys = tds[3].css('.product-catalogue__key::text').getall()
            test_type = [self.TYPE_MAPPING.get(k.strip()) for k in keys if k.strip() in self.TYPE_MAPPING]

            yield scrapy.Request(
                url=absolute_link, 
                callback=self.parse_item,
                meta={
                    'remote_support': remote_support,
                    'adaptive_support': adaptive_support,
                    'test_type': test_type,
                    'type_id': type_id
                },
                dont_filter=True
            )
        
        # --- STRICT DISABLED CHECK ---
        next_button = response.css('li.pagination__item.-arrow.-next')
        
        is_disabled = False
        if not next_button or '-disabled' in next_button.attrib.get('class', ''):
            is_disabled = True

        if not is_disabled and len(rows) > 0:
            next_start = start_index + 12
            next_url = f"https://www.shl.com/products/product-catalog/?start={next_start}&type={type_id}"
            
            self.logger.info(f"➡️ Moving to next page: {next_url}")
            yield scrapy.Request(
                url=next_url, 
                callback=self.parse, 
                meta={'start_index': next_start, 'type_id': type_id},
                dont_filter=True
            )
        else:
            self.logger.info(f"🛑 Next button disabled/missing. End of Type {type_id}.")
            self.flush_batch()
            
            self.logger.info("🔄 SWITCHING TO TYPE 2 PROCESSING...")
            start_url_type_2 = "https://www.shl.com/products/product-catalog/?start=0&type=2"
            yield scrapy.Request(
                url=start_url_type_2, 
                callback=self.parse, 
                meta={'start_index': 0, 'type_id': 2},
                dont_filter=True
            )

    def parse_item(self, response):
        type_id = response.meta['type_id']
        raw_name = response.css("h1::text").get(default="").strip()
        
        if not raw_name:
            return
            
        raw_desc = " ".join(response.xpath('//h4[contains(text(), "Description")]/following-sibling::p//text()').getall()).strip()
        if not raw_desc:
            raw_desc = " ".join(response.css("body p::text, body li::text").getall()).strip()
            
        duration_text = response.xpath('//p[contains(text(), "Approximate Completion Time")]/text()').get(default="")
        duration_match = re.search(r'(\d+)', duration_text)
        duration = int(duration_match.group(1)) if duration_match else 0

        item = {
            "type": type_id,
            "name": raw_name,
            "url": response.url,
            "description": re.sub(r'\s+', ' ', raw_desc).strip(),
            "duration": duration,
            "test_type": response.meta.get('test_type', []),
            "adaptive_support": response.meta.get('adaptive_support', "No"),
            "remote_support": response.meta.get('remote_support', "No")
        }

        self.batch.append(item)
        if len(self.batch) >= 12:
            self.flush_batch()

    def flush_batch(self):
        if not self.batch:
            return
            
        self.logger.info(f"💾 Saving batch of {len(self.batch)} items to disk...")
        with open(self.file_path, mode='a', encoding='utf-8') as f:
            for item in self.batch:
                f.write(json.dumps(item) + '\n')
                
        self.batch.clear()

    def closed(self, reason):
        if self.batch:
            self.logger.info(f"🧹 Flushing final {len(self.batch)} items to disk...")
            self.flush_batch()
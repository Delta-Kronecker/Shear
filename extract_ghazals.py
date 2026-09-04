import requests
from bs4 import BeautifulSoup
import time
import os
import json
from datetime import datetime
from typing import List, Dict, Optional

class GhazalWorkflow:
    def __init__(self, start: int = 1, end: int = 3230, delay: float = 0.3):
        self.start = start
        self.end = end
        self.delay = delay
        self.base_url = "https://ganjoor.net/moulavi/shams/ghazalsh/sh"
        self.ghazals = []
        self.failed = []
        self.extracted_count = 0
        
    def step1_validate_range(self) -> bool:
        print("\n[STEP 1] Validating range...")
        if self.start < 1 or self.end > 3230 or self.start > self.end:
            print(f"ERROR: Invalid range {self.start}-{self.end}")
            return False
        print(f"OK: Range {self.start}-{self.end} is valid")
        print(f"Total ghazals to process: {self.end - self.start + 1}")
        return True
    
    def step2_create_directories(self) -> bool:
        print("\n[STEP 2] Creating directories...")
        try:
            os.makedirs('output', exist_ok=True)
            os.makedirs('output/ghazals', exist_ok=True)
            print("OK: Directories created")
            return True
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return False
    
    def step3_fetch_single_ghazal(self, url: str, number: int) -> Optional[Dict]:
        try:
            response = requests.get(url, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            poem_div = soup.find('div', class_='poem')
            if not poem_div:
                poem_div = soup.find('div', class_='b')
            
            if not poem_div:
                return None
                
            verses = []
            for verse in poem_div.find_all('div', class_='b'):
                m1 = verse.find('div', class_='m1')
                m2 = verse.find('div', class_='m2')
                if m1 and m2:
                    verses.append({
                        'first': m1.get_text(strip=True),
                        'second': m2.get_text(strip=True)
                    })
            
            title_tag = soup.find('h1') or soup.find('h2')
            title = title_tag.get_text(strip=True) if title_tag else f"غزل شماره {number}"
            
            return {
                'number': number,
                'title': title,
                'verses': verses,
                'total_verses': len(verses),
                'url': url
            }
            
        except Exception as e:
            print(f"ERROR fetching {number}: {str(e)}")
            return None
    
    def step4_process_all_ghazals(self) -> bool:
        print("\n[STEP 4] Processing ghazals...")
        print(f"Starting from {self.start} to {self.end}")
        
        for i in range(self.start, self.end + 1):
            url = f"{self.base_url}{i}"
            print(f"  [{i}/{self.end}] Processing ghazal {i}...", end=" ")
            
            ghazal_data = self.step3_fetch_single_ghazal(url, i)
            
            if ghazal_data and ghazal_data['verses']:
                self.ghazals.append(ghazal_data)
                self.extracted_count += 1
                print(f"OK ({ghazal_data['total_verses']} verses)")
            else:
                self.failed.append(i)
                print("FAILED")
            
            time.sleep(self.delay)
        
        print(f"\nOK: Processed {len(self.ghazals)} ghazals successfully")
        print(f"Failed: {len(self.failed)} ghazals")
        return True
    
    def step5_sort_ghazals(self) -> bool:
        print("\n[STEP 5] Sorting ghazals...")
        self.ghazals.sort(key=lambda x: x['number'])
        print("OK: Sorted by number")
        return True
    
    def step6_generate_markdown(self) -> str:
        print("\n[STEP 6] Generating Markdown...")
        
        md_lines = []
        
        md_lines.append("# دیوان شمس تبریزی - غزلیات\n")
        md_lines.append(f"**تعداد کل غزل‌ها:** {len(self.ghazals)}\n")
        md_lines.append(f"**محدوده:** {self.start} تا {self.end}\n")
        md_lines.append(f"**تاریخ تولید:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        md_lines.append("---\n")
        
        md_lines.append("## فهرست مطالب\n")
        for ghazal in self.ghazals:
            md_lines.append(f"- [غزل {ghazal['number']}: {ghazal['title']}](#ghazal-{ghazal['number']})")
        md_lines.append("\n---\n")
        
        for ghazal in self.ghazals:
            md_lines.append(f"## غزل {ghazal['number']}")
            md_lines.append(f"**عنوان:** {ghazal['title']}")
            md_lines.append(f"**تعداد ابیات:** {ghazal['total_verses']}")
            md_lines.append(f"**منبع:** [{ghazal['url']}]({ghazal['url']})\n")
            
            md_lines.append("```")
            for verse in ghazal['verses']:
                md_lines.append(f"{verse['first']}")
                md_lines.append(f"{verse['second']}")
                md_lines.append("")
            md_lines.append("```\n")
            
            md_lines.append("---\n")
        
        print("OK: Markdown generated")
        return "\n".join(md_lines)
    
    def step7_save_markdown(self, content: str) -> bool:
        print("\n[STEP 7] Saving Markdown file...")
        try:
            with open('output/ghazals_complete.md', 'w', encoding='utf-8') as f:
                f.write(content)
            with open('ghazals_complete.md', 'w', encoding='utf-8') as f:
                f.write(content)
            print("OK: Saved to output/ghazals_complete.md and root")
            return True
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return False
    
    def step8_save_json_backup(self) -> bool:
        print("\n[STEP 8] Saving JSON backup...")
        try:
            with open('output/ghazals_backup.json', 'w', encoding='utf-8') as f:
                json.dump(self.ghazals, f, ensure_ascii=False, indent=2)
            print("OK: Saved to output/ghazals_backup.json")
            return True
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return False
    
    def step9_save_failed_log(self) -> bool:
        print("\n[STEP 9] Saving failed log...")
        try:
            with open('output/failed_ghazals.txt', 'w', encoding='utf-8') as f:
                f.write(f"Failed ghazals (total: {len(self.failed)}):\n")
                for num in self.failed:
                    f.write(f"{num}\n")
            print(f"OK: Saved {len(self.failed)} failed entries")
            return True
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return False
    
    def step10_generate_report(self) -> bool:
        print("\n[STEP 10] Generating final report...")
        
        report_lines = []
        report_lines.append("="*60)
        report_lines.append("WORKFLOW COMPLETED SUCCESSFULLY")
        report_lines.append("="*60)
        report_lines.append(f"Start range: {self.start}")
        report_lines.append(f"End range: {self.end}")
        report_lines.append(f"Total processed: {len(self.ghazals)}")
        report_lines.append(f"Total failed: {len(self.failed)}")
        success_rate = round((len(self.ghazals)/(self.end-self.start+1))*100, 2) if self.end-self.start+1 > 0 else 0
        report_lines.append(f"Success rate: {success_rate}%")
        report_lines.append(f"Output directory: output/")
        report_lines.append("Files created:")
        report_lines.append("  - ghazals_complete.md (Main Markdown)")
        report_lines.append("  - ghazals_backup.json (JSON backup)")
        report_lines.append("  - failed_ghazals.txt (Failed list)")
        report_lines.append("="*60)
        
        print("\n".join(report_lines))
        
        with open('output/workflow_report.txt', 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
        
        with open('workflow_report.txt', 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
        
        print("OK: Reports saved")
        return True
    
    def run_workflow(self):
        print("\n" + "="*60)
        print("RUMI GHAZAL EXTRACTOR - COMPLETE WORKFLOW")
        print("="*60)
        
        if not self.step1_validate_range():
            return False
        
        if not self.step2_create_directories():
            return False
        
        if not self.step4_process_all_ghazals():
            return False
        
        self.step5_sort_ghazals()
        
        markdown_content = self.step6_generate_markdown()
        self.step7_save_markdown(markdown_content)
        self.step8_save_json_backup()
        self.step9_save_failed_log()
        self.step10_generate_report()
        
        print("\n" + "="*60)
        print("WORKFLOW COMPLETED - ALL STEPS SUCCESSFUL")
        print("="*60)
        return True


def main():
    workflow = GhazalWorkflow(start=1, end=3230, delay=0.3)
    workflow.run_workflow()


if __name__ == "__main__":
    main()

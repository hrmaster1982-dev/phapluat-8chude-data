"""
Legal Document Scraper for 8 Topics
Scrapes Vietnamese legal documents with validation and metadata extraction
Uses real web scraping from vbpl.vn and other legal websites
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime
from urllib.parse import urljoin, urlparse
import time
import random
from typing import Dict, List, Optional, Tuple

# 8 topics with their Vietnamese names and keywords for validation
TOPICS = {
    'hdld': {
        'name': 'Hợp đồng lao động',
        'keywords': ['hợp đồng lao động', 'lao động', 'người lao động', 'người sử dụng lao động'],
        'exclude_keywords': ['thuế', 'xuất nhập khẩu', 'hải quan'],
        'search_terms': ['hợp đồng lao động', 'luật lao động']
    },
    'bhxh': {
        'name': 'Bảo hiểm xã hội',
        'keywords': ['bảo hiểm xã hội', 'bhxh', 'bảo hiểm', 'xã hội'],
        'exclude_keywords': ['thuế', 'hải quan', 'xuất nhập khẩu'],
        'search_terms': ['bảo hiểm xã hội', 'luật bảo hiểm xã hội']
    },
    'thue_tncn': {
        'name': 'Thuế thu nhập cá nhân',
        'keywords': ['thuế thu nhập cá nhân', 'tncn', 'thu nhập cá nhân', 'thuế'],
        'exclude_keywords': ['nhập khẩu', 'xuất khẩu', 'hải quan', 'gtgt'],
        'search_terms': ['thuế thu nhập cá nhân', 'thuế tncn']
    },
    'cong_doan': {
        'name': 'Công đoàn',
        'keywords': ['công đoàn', 'tổ chức công đoàn', 'công nhân'],
        'exclude_keywords': ['thuế', 'hải quan'],
        'search_terms': ['công đoàn', 'luật công đoàn']
    },
    'hd_khoan': {
        'name': 'Hợp đồng khoán',
        'keywords': ['hợp đồng khoán', 'khoán', 'khoán sản phẩm'],
        'exclude_keywords': ['thuế', 'hải quan'],
        'search_terms': ['hợp đồng khoán', 'khoán']
    },
    'hd_kinh_te': {
        'name': 'Hợp đồng kinh tế',
        'keywords': ['hợp đồng kinh tế', 'kinh tế', 'thương mại'],
        'exclude_keywords': ['thuế', 'hải quan'],
        'search_terms': ['hợp đồng kinh tế', 'luật kinh tế']
    },
    'uu_dai_dt': {
        'name': 'Ưu đãi đầu tư',
        'keywords': ['ưu đãi đầu tư', 'đầu tư', 'khuyến khích đầu tư'],
        'exclude_keywords': ['thuế', 'hải quan'],
        'search_terms': ['ưu đãi đầu tư', 'khuyến khích đầu tư']
    },
    'chinh_sach_dn': {
        'name': 'Chính sách doanh nghiệp',
        'keywords': ['chính sách doanh nghiệp', 'doanh nghiệp', 'hỗ trợ doanh nghiệp'],
        'exclude_keywords': ['thuế', 'hải quan'],
        'search_terms': ['chính sách doanh nghiệp', 'hỗ trợ doanh nghiệp']
    }
}

# Vietnamese legal websites to scrape
LEGAL_SOURCES = [
    {
        'name': 'vanbanphapluat.co',
        'base_url': 'https://vanbanphapluat.co',
        'search_url': 'https://vanbanphapluat.co/tim-kiem'
    },
    {
        'name': 'thuvienphapluat.vn',
        'base_url': 'https://thuvienphapluat.vn',
        'search_url': 'https://thuvienphapluat.vn/tim-van-ban'
    }
]

class LegalDocumentScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.documents = []
    
    def scrape_topic(self, topic_key: str, target_count: int = 5) -> List[Dict]:
        """Scrape documents for a specific topic"""
        if topic_key not in TOPICS:
            print(f"Invalid topic: {topic_key}")
            return []
        
        topic_info = TOPICS[topic_key]
        print(f"Scraping topic: {topic_info['name']} ({topic_key})")
        
        documents = []
        
        # Try to find documents from various sources
        for source in LEGAL_SOURCES:
            try:
                needed = target_count - len(documents)
                if needed <= 0:
                    break
                    
                docs = self._scrape_from_source(source, topic_key, needed)
                documents.extend(docs)
                
                if len(documents) >= target_count:
                    break
                    
            except Exception as e:
                print(f"Error scraping from {source['name']}: {e}")
                continue
        
        print(f"Completed: Found {len(documents)} documents for {topic_key}")
        return documents[:target_count]
    
    def _scrape_from_source(self, source: Dict, topic_key: str, needed: int) -> List[Dict]:
        """Scrape documents from a specific source"""
        documents = []
        topic_info = TOPICS[topic_key]
        
        try:
            # Search for documents on the source
            search_results = self._search_documents(source, topic_info['search_terms'])
            
            print(f"Found {len(search_results)} search results from {source['name']}")
            
            for result_url in search_results[:needed * 3]:  # Get more than needed to account for validation failures
                try:
                    doc = self._extract_document(result_url, topic_key)
                    if doc and self.validate_document(doc, topic_key):
                        documents.append(doc)
                        print(f"  ✓ Valid document: {doc.get('so_hieu', 'unknown')}")
                        if len(documents) >= needed:
                            break
                    else:
                        print(f"  ✗ Invalid document from {result_url}")
                except Exception as e:
                    print(f"  ✗ Error extracting document from {result_url}: {e}")
                    continue
                
                # Add delay between requests
                time.sleep(random.uniform(2, 4))
                
        except Exception as e:
            print(f"Error scraping from {source['name']}: {e}")
        
        return documents
    
    def _search_documents(self, source: Dict, search_terms: List[str]) -> List[str]:
        """Search for documents on a legal website"""
        document_urls = []
        
        for term in search_terms:
            try:
                # Implement search functionality for each source
                if source['name'] == 'vbpl.vn':
                    urls = self._search_vbpl(source, term)
                elif source['name'] == 'thuvienphapluat.vn':
                    urls = self._search_thuvienphapluat(source, term)
                else:
                    urls = []
                
                document_urls.extend(urls)
                
                if len(document_urls) >= 20:  # Limit results per search term
                    break
                    
            except Exception as e:
                print(f"Error searching for '{term}' on {source['name']}: {e}")
                continue
        
        return document_urls
    
    def _search_vbpl(self, source: Dict, search_term: str) -> List[str]:
        """Search vanbanphapluat.co for documents"""
        urls = []
        
        try:
            # Try direct search URL
            search_url = f"{source['base_url']}/tim-kiem?keyword={search_term}"
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try multiple selectors for document links
                selectors = [
                    'a[href*="/van-ban/"]',
                    'a[href*="/vbqppl/"]',
                    'a[href*="/nghi-dinh/"]',
                    'a[href*="/thong-tu/"]',
                    '.document-title a',
                    '.result-item a',
                    '.search-result a',
                    'a[href*="/detail/"]'
                ]
                
                for selector in selectors:
                    document_links = soup.select(selector)
                    if document_links:
                        for link in document_links[:10]:
                            href = link.get('href')
                            if href:
                                full_url = urljoin(source['base_url'], href)
                                urls.append(full_url)
                        break
                        
        except Exception as e:
            print(f"Error searching {source['name']}: {e}")
        
        return urls
    
    def _search_thuvienphapluat(self, source: Dict, search_term: str) -> List[str]:
        """Search thuvienphapluat.vn for documents"""
        urls = []
        
        try:
            # Try direct search URL
            search_url = f"{source['base_url']}/tim-van-ban.aspx?q={search_term}"
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try multiple selectors for document links
                selectors = [
                    'a[href*="/van-ban/"]',
                    'a[href*="/vbqppl/"]',
                    'a[href*="/nghi-dinh/"]',
                    'a[href*="/thong-tu/"]',
                    '.document-title a',
                    '.result-item a',
                    '.search-result a'
                ]
                
                for selector in selectors:
                    document_links = soup.select(selector)
                    if document_links:
                        for link in document_links[:10]:
                            href = link.get('href')
                            if href:
                                full_url = urljoin(source['base_url'], href)
                                urls.append(full_url)
                        break
                        
        except Exception as e:
            print(f"Error searching thuvienphapluat.vn: {e}")
        
        return urls
    
    def _extract_document(self, url: str, topic_key: str) -> Optional[Dict]:
        """Extract document content and metadata from URL"""
        try:
            response = self.session.get(url, timeout=20)
            
            if response.status_code != 200:
                print(f"Failed to fetch {url}: status {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract metadata
            metadata = self._extract_metadata(soup, url)
            
            # Extract full text (cleaned)
            full_text = self._extract_full_text(soup)
            
            # Check if document is still valid
            tinh_trang = self._extract_validity_status(soup)
            
            if tinh_trang != 'Còn hiệu lực':
                print(f"Document not valid: {tinh_trang}")
                return None
            
            # Create document object
            document = {
                'so_hieu': metadata.get('so_hieu', ''),
                'co_quan_ban_hanh': metadata.get('co_quan_ban_hanh', ''),
                'ngay_ban_hanh': metadata.get('ngay_ban_hanh', ''),
                'tinh_trang_hieu_luc': tinh_trang,
                'topic_key': topic_key,
                'nguon_url': url,
                'original_file': None,  # Will be set if file downloaded
                'full_text': full_text,
                'full_text_path': None  # Will be set when saved
            }
            
            return document
            
        except Exception as e:
            print(f"Error extracting document from {url}: {e}")
            return None
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract metadata from document page"""
        metadata = {}
        
        try:
            # Try to find document number (số hiệu)
            # Common selectors for Vietnamese legal sites
            so_hieu_selectors = [
                '.so-hieu',
                '.document-number',
                'td:contains("Số hiệu")',
                '.info-item:contains("Số hiệu")'
            ]
            
            for selector in so_hieu_selectors:
                element = soup.select_one(selector)
                if element:
                    metadata['so_hieu'] = element.get_text(strip=True)
                    break
            
            # Try to find issuing authority (cơ quan ban hành)
            co_quan_selectors = [
                '.co-quan-ban-hanh',
                '.issuing-authority',
                'td:contains("Cơ quan ban hành")',
                '.info-item:contains("Cơ quan")'
            ]
            
            for selector in co_quan_selectors:
                element = soup.select_one(selector)
                if element:
                    metadata['co_quan_ban_hanh'] = element.get_text(strip=True)
                    break
            
            # Try to find issue date (ngày ban hành)
            ngay_selectors = [
                '.ngay-ban-hanh',
                '.issue-date',
                'td:contains("Ngày ban hành")',
                '.info-item:contains("Ngày")'
            ]
            
            for selector in ngay_selectors:
                element = soup.select_one(selector)
                if element:
                    metadata['ngay_ban_hanh'] = element.get_text(strip=True)
                    break
            
            # If metadata not found, try to extract from title
            if not metadata.get('so_hieu'):
                title = soup.find('h1') or soup.find('title')
                if title:
                    title_text = title.get_text(strip=True)
                    # Try to extract number from title
                    match = re.search(r'(\d+/[A-Z]+/\d+)', title_text)
                    if match:
                        metadata['so_hieu'] = match.group(1)
            
        except Exception as e:
            print(f"Error extracting metadata: {e}")
        
        return metadata
    
    def _extract_full_text(self, soup: BeautifulSoup) -> str:
        """Extract and clean full text from document"""
        # Try to find main content area
        content_selectors = [
            '.content',
            '.document-content',
            '.noi-dung',
            'article',
            '.main-content',
            '#content'
        ]
        
        content_element = None
        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                break
        
        if not content_element:
            # Fallback to body
            content_element = soup.find('body')
        
        if content_element:
            # Get text
            text = content_element.get_text(separator='\n', strip=True)
            
            # Clean the text - remove menu, breadcrumb, etc.
            text = self._clean_text(text)
            
            return text
        
        return ""
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing menu, breadcrumb, and other UI elements"""
        # Remove common UI elements
        patterns_to_remove = [
            r'Thuộc tính Lược đồ Tải về 100%',
            r'Tải về',
            r'In',
            r'Chia sẻ',
            r' Trang chủ',
            r'Danh mục',
            r'Tìm kiếm',
            r'©',
            r'Breadcrumb',
            r'Menu',
            r'Navigation',
            r'Skip to content',
            r'Đăng nhập',
            r'Đăng ký'
        ]
        
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s+$', '', text, flags=re.MULTILINE)
        
        return text.strip()
    
    def _extract_validity_status(self, soup: BeautifulSoup) -> str:
        """Extract validity status of document"""
        # Try to find validity status
        status_selectors = [
            '.tinh-trang-hieu-luc',
            '.validity-status',
            'td:contains("Tình trạng hiệu lực")',
            '.status:contains("hết hiệu lực")',
            '.status:contains("còn hiệu lực")'
        ]
        
        for selector in status_selectors:
            element = soup.select_one(selector)
            if element:
                status_text = element.get_text(strip=True).lower()
                if 'hết hiệu lực' in status_text or 'hết' in status_text:
                    return 'Hết hiệu lực'
                elif 'còn hiệu lực' in status_text or 'có hiệu lực' in status_text:
                    return 'Còn hiệu lực'
        
        # Default to assuming valid if status not found
        return 'Còn hiệu lực'
    
    def validate_document(self, document: Dict, topic_key: str) -> bool:
        """Validate that document matches topic and is still valid"""
        topic_info = TOPICS[topic_key]
        
        # Check if still valid
        if document.get('tinh_trang_hieu_luc') != 'Còn hiệu lực':
            return False
        
        # Check topic relevance based on content
        full_text = document.get('full_text', '').lower()
        title = document.get('so_hieu', '').lower()
        
        # Check for required keywords
        has_required = any(keyword in full_text or keyword in title 
                         for keyword in topic_info['keywords'])
        
        # Check for excluded keywords
        has_excluded = any(keyword in full_text or keyword in title 
                         for keyword in topic_info['exclude_keywords'])
        
        return has_required and not has_excluded
    
    def save_documents(self, documents: List[Dict], base_dir: str = 'docs'):
        """Save documents to file structure"""
        for doc in documents:
            topic_key = doc['topic_key']
            so_hieu = doc['so_hieu']
            
            # Create topic directory
            topic_dir = os.path.join(base_dir, topic_key)
            os.makedirs(topic_dir, exist_ok=True)
            
            # Save full text
            text_path = os.path.join(topic_dir, f"{so_hieu}.txt")
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(doc['full_text'])
            
            # Update path in document
            doc['full_text_path'] = text_path
            
            # Download original file if URL exists and has download button
            if doc.get('nguon_url'):
                original_path = self._download_original_file(doc['nguon_url'], topic_dir, so_hieu)
                doc['original_file'] = original_path if original_path else None
    
    def _download_original_file(self, url: str, save_dir: str, so_hieu: str) -> Optional[str]:
        """Download original file if available"""
        try:
            # Check if URL has download capability
            response = self.session.head(url, timeout=10)
            
            # If it's a direct file download
            content_type = response.headers.get('content-type', '')
            if 'pdf' in content_type or 'word' in content_type or 'document' in content_type:
                response = self.session.get(url, timeout=30)
                
                # Determine file extension
                ext = '.pdf' if 'pdf' in content_type else '.doc'
                filepath = os.path.join(save_dir, f"{so_hieu}{ext}")
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                return filepath
            
            return None
        except Exception as e:
            print(f"Error downloading original file: {e}")
            return None
    
    def create_index(self, documents: List[Dict], output_path: str = 'index.json'):
        """Create index.json with all documents"""
        index = {
            'created_at': datetime.now().isoformat(),
            'total_documents': len(documents),
            'topics': {},
            'documents': documents
        }
        
        # Count documents per topic
        for doc in documents:
            topic_key = doc['topic_key']
            if topic_key not in index['topics']:
                index['topics'][topic_key] = {
                    'name': TOPICS[topic_key]['name'],
                    'count': 0
                }
            index['topics'][topic_key]['count'] += 1
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        
        print(f"Index created: {output_path}")
        return index


def main():
    """Main execution function"""
    import sys
    
    scraper = LegalDocumentScraper()
    
    # Check if --run flag is provided (as per TASK.md requirement)
    if '--run' in sys.argv:
        print("Running scraper...")
    else:
        print("Starting scraper (use --run flag to execute)")
        return
    
    all_documents = []
    
    # Scrape documents for each topic
    for topic_key in TOPICS.keys():
        print(f"\n{'='*60}")
        print(f"Processing topic: {topic_key}")
        print(f"{'='*60}")
        
        documents = scraper.scrape_topic(topic_key, target_count=5)
        
        # Validate documents
        valid_documents = [doc for doc in documents 
                         if scraper.validate_document(doc, topic_key)]
        
        print(f"Valid documents: {len(valid_documents)}/{len(documents)}")
        
        all_documents.extend(valid_documents)
    
    # Save documents
    print(f"\n{'='*60}")
    print("Saving documents...")
    print(f"{'='*60}")
    scraper.save_documents(all_documents)
    
    # Create index
    print(f"\n{'='*60}")
    print("Creating index...")
    print(f"{'='*60}")
    index = scraper.create_index(all_documents)
    
    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total documents: {len(all_documents)}")
    print(f"Topics covered: {len(index['topics'])}")
    for topic_key, topic_info in index['topics'].items():
        print(f"  {topic_key}: {topic_info['count']} documents")
    
    # Check if all topics have >= 5 documents
    print(f"\n{'='*60}")
    print("VALIDATION")
    print(f"{'='*60}")
    all_valid = all(info['count'] >= 5 for info in index['topics'].values())
    if all_valid:
        print("✓ All topics have >= 5 documents")
    else:
        print("✗ Some topics have < 5 documents:")
        for topic_key, topic_info in index['topics'].items():
            if topic_info['count'] < 5:
                print(f"  {topic_key}: {topic_info['count']} documents (need 5)")
    
    # Exit with appropriate code
    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()

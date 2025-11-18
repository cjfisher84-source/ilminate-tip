"""
Image & QR Code Scanner for APEX Detection Engine

Multi-layer image analysis combining:
- QR code detection (quishing attacks)
- Logo impersonation detection
- Screenshot phishing detection
- OCR for text extraction
- AI-based image analysis

Author: Ilminate Security Team
Version: 2.0.0
"""

import logging
import base64
import hashlib
from typing import Dict, List, Optional, Tuple
from io import BytesIO
from dataclasses import dataclass
import numpy as np

# Image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL/Pillow not available")

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logging.warning("OpenCV not available")

# QR code detection - Traditional (fast, reliable)
try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False
    logging.warning("pyzbar not available - QR code detection limited")

# QR code detection - AI-based (for difficult cases)
try:
    from qreader import QReader
    QREADER_AVAILABLE = True
except ImportError:
    QREADER_AVAILABLE = False
    logging.warning("qreader not available - advanced QR detection unavailable")

# OCR (text extraction)
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("Tesseract not available - OCR unavailable")

# AI Vision (logo detection, image classification)
try:
    from transformers import CLIPProcessor, CLIPModel
    import torch
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    logging.warning("CLIP not available - AI vision features limited")


logger = logging.getLogger('ilminate.apex.image_scanner')


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class QRCodeResult:
    """QR code detection result"""
    detected: bool
    data: Optional[str]
    type: str  # 'QRCODE', 'DATAMATRIX', etc.
    position: Optional[Tuple[int, int, int, int]]  # x, y, width, height
    url: Optional[str]  # Extracted URL if present
    detection_method: str  # 'pyzbar', 'qreader', 'hybrid'


@dataclass
class LogoDetectionResult:
    """Logo/brand detection result"""
    detected: bool
    brand: Optional[str]
    confidence: float
    is_impersonation: bool
    legitimate_domains: List[str]
    email_sender_domain: Optional[str]


@dataclass
class ImageAnalysisResult:
    """Complete image analysis result"""
    has_qr_code: bool
    qr_codes: List[QRCodeResult]
    has_logo: bool
    logo_detection: Optional[LogoDetectionResult]
    has_text: bool
    extracted_text: Optional[str]
    is_screenshot: bool
    is_suspicious: bool
    threat_score: float  # 0-1
    indicators: List[str]


# ============================================================================
# QR Code Scanner
# ============================================================================

class QRCodeScanner:
    """
    Multi-method QR code scanner
    
    Uses multiple detection methods:
    1. pyzbar (fast, traditional)
    2. qreader (AI-based, for difficult cases)
    3. OpenCV preprocessing (enhance detection)
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.use_ai = config.get('use_ai_detection', True)
        
        # Initialize AI-based reader if available
        if QREADER_AVAILABLE and self.use_ai:
            self.ai_reader = QReader()
            logger.info("QR Code AI reader (YOLOv8) initialized")
        else:
            self.ai_reader = None
        
        # Known malicious QR code patterns
        self.malicious_patterns = [
            r'bit\.ly',
            r'tinyurl\.com',
            r'\.tk$',
            r'\.ml$',
            r'\.ga$',
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',  # IP addresses
        ]
        
        logger.info("QR Code Scanner initialized")
    
    def scan_image(self, image_data: bytes) -> List[QRCodeResult]:
        """
        Scan image for QR codes using multiple methods
        
        Args:
            image_data: Image bytes
            
        Returns:
            List of QR code detection results
        """
        results = []
        
        # Convert to PIL Image
        try:
            pil_image = Image.open(BytesIO(image_data))
        except Exception as e:
            logger.error(f"Error opening image: {e}")
            return results
        
        # Method 1: pyzbar (fast, traditional)
        if PYZBAR_AVAILABLE:
            pyzbar_results = self._scan_with_pyzbar(pil_image)
            results.extend(pyzbar_results)
        
        # Method 2: AI-based detection (for difficult cases)
        if self.ai_reader and len(results) == 0:
            # Only use AI if traditional method found nothing
            ai_results = self._scan_with_ai(pil_image)
            results.extend(ai_results)
        
        # Method 3: Try with preprocessing if still nothing found
        if len(results) == 0 and OPENCV_AVAILABLE:
            preprocessed = self._preprocess_image(pil_image)
            if PYZBAR_AVAILABLE:
                results.extend(self._scan_with_pyzbar(preprocessed))
        
        return results
    
    def _scan_with_pyzbar(self, image: Image.Image) -> List[QRCodeResult]:
        """Scan with pyzbar (traditional method)"""
        results = []
        
        try:
            # Convert PIL to numpy array for pyzbar
            image_array = np.array(image)
            
            # Decode QR codes
            decoded_objects = pyzbar.decode(image_array)
            
            for obj in decoded_objects:
                data = obj.data.decode('utf-8', errors='ignore')
                
                # Extract URL if present
                url = self._extract_url(data)
                
                # Get position
                rect = obj.rect
                position = (rect.left, rect.top, rect.width, rect.height)
                
                result = QRCodeResult(
                    detected=True,
                    data=data,
                    type=obj.type,
                    position=position,
                    url=url,
                    detection_method='pyzbar'
                )
                results.append(result)
                
                logger.info(f"QR code detected (pyzbar): {data[:50]}...")
                
        except Exception as e:
            logger.error(f"pyzbar scan error: {e}")
        
        return results
    
    def _scan_with_ai(self, image: Image.Image) -> List[QRCodeResult]:
        """Scan with AI-based reader (for difficult cases)"""
        results = []
        
        try:
            # qreader expects file path or PIL Image
            decoded_data = self.ai_reader.detect_and_decode(image=image)
            
            if decoded_data:
                # qreader can return single result or list
                if not isinstance(decoded_data, list):
                    decoded_data = [decoded_data]
                
                for data in decoded_data:
                    if data:  # Filter out None/empty results
                        url = self._extract_url(data)
                        
                        result = QRCodeResult(
                            detected=True,
                            data=data,
                            type='QRCODE',
                            position=None,  # qreader doesn't provide position
                            url=url,
                            detection_method='qreader_ai'
                        )
                        results.append(result)
                        
                        logger.info(f"QR code detected (AI): {data[:50]}...")
                        
        except Exception as e:
            logger.error(f"AI QR reader error: {e}")
        
        return results
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image to improve QR code detection"""
        try:
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Denoise
            denoised = cv2.fastNlMeansDenoising(binary)
            
            # Convert back to PIL
            return Image.fromarray(denoised)
            
        except Exception as e:
            logger.error(f"Image preprocessing error: {e}")
            return image
    
    def _extract_url(self, data: str) -> Optional[str]:
        """Extract URL from QR code data"""
        import re
        
        # Try to find URL pattern
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        match = re.search(url_pattern, data)
        
        if match:
            return match.group(0)
        
        # If data looks like a URL (starts with http)
        if data.startswith(('http://', 'https://')):
            return data
        
        return None
    
    def analyze_qr_code(self, qr_result: QRCodeResult) -> Dict:
        """
        Analyze QR code for threats
        
        Returns:
            {
                'is_suspicious': bool,
                'threat_score': float,
                'indicators': list,
                'url_analysis': dict
            }
        """
        indicators = []
        threat_score = 0.0
        
        if not qr_result.url:
            return {
                'is_suspicious': False,
                'threat_score': 0.0,
                'indicators': [],
                'url_analysis': {}
            }
        
        url = qr_result.url
        
        # Check for malicious patterns
        import re
        for pattern in self.malicious_patterns:
            if re.search(pattern, url):
                indicators.append(f"Suspicious URL pattern: {pattern}")
                threat_score += 0.3
        
        # Check URL length (phishing often uses very long URLs)
        if len(url) > 100:
            indicators.append("Unusually long URL")
            threat_score += 0.2
        
        # Check for IP address instead of domain
        if re.match(r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url):
            indicators.append("Uses IP address instead of domain")
            threat_score += 0.4
        
        # Check for URL shortener
        if any(s in url for s in ['bit.ly', 'tinyurl', 'short', 'tiny']):
            indicators.append("URL shortener detected")
            threat_score += 0.3
        
        threat_score = min(threat_score, 1.0)
        
        return {
            'is_suspicious': threat_score > 0.5,
            'threat_score': threat_score,
            'indicators': indicators,
            'url_analysis': {
                'url': url,
                'length': len(url),
                'has_shortener': any(s in url for s in ['bit.ly', 'tinyurl'])
            }
        }


# ============================================================================
# Logo Detection (Brand Impersonation)
# ============================================================================

class LogoDetector:
    """
    Detect logos and brands in images
    Uses CLIP for zero-shot logo detection
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.model = None
        self.processor = None
        
        if CLIP_AVAILABLE:
            try:
                self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                logger.info("CLIP model loaded for logo detection")
            except Exception as e:
                logger.error(f"Error loading CLIP model: {e}")
        
        # Known legitimate brand domains
        self.brand_domains = {
            'microsoft': ['microsoft.com', 'office.com', 'outlook.com', 'live.com'],
            'google': ['google.com', 'gmail.com', 'youtube.com'],
            'apple': ['apple.com', 'icloud.com', 'me.com'],
            'amazon': ['amazon.com', 'aws.amazon.com'],
            'paypal': ['paypal.com'],
            'facebook': ['facebook.com', 'fb.com', 'instagram.com'],
            'linkedin': ['linkedin.com'],
            'twitter': ['twitter.com', 'x.com'],
        }
    
    def detect_logo(
        self, 
        image_data: bytes, 
        sender_domain: Optional[str] = None
    ) -> LogoDetectionResult:
        """
        Detect logo/brand in image and check for impersonation
        """
        if not CLIP_AVAILABLE or not self.model:
            return LogoDetectionResult(
                detected=False,
                brand=None,
                confidence=0.0,
                is_impersonation=False,
                legitimate_domains=[],
                email_sender_domain=sender_domain
            )
        
        try:
            # Load image
            image = Image.open(BytesIO(image_data))
            
            # Brands to check for
            brands = list(self.brand_domains.keys())
            
            # Create text prompts
            texts = [f"a {brand} logo" for brand in brands] + ["no logo", "other image"]
            
            # Process with CLIP
            inputs = self.processor(
                text=texts, 
                images=image, 
                return_tensors="pt", 
                padding=True
            )
            
            outputs = self.model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)
            
            # Get best match
            max_prob_idx = probs.argmax().item()
            max_prob = probs[0][max_prob_idx].item()
            
            # If detected a known brand
            if max_prob_idx < len(brands) and max_prob > 0.3:
                detected_brand = brands[max_prob_idx]
                legitimate_domains = self.brand_domains[detected_brand]
                
                # Check for impersonation
                is_impersonation = False
                if sender_domain:
                    # Check if sender domain matches legitimate domains
                    is_legitimate = any(
                        sender_domain.endswith(domain) 
                        for domain in legitimate_domains
                    )
                    is_impersonation = not is_legitimate
                
                return LogoDetectionResult(
                    detected=True,
                    brand=detected_brand,
                    confidence=max_prob,
                    is_impersonation=is_impersonation,
                    legitimate_domains=legitimate_domains,
                    email_sender_domain=sender_domain
                )
            
        except Exception as e:
            logger.error(f"Logo detection error: {e}")
        
        return LogoDetectionResult(
            detected=False,
            brand=None,
            confidence=0.0,
            is_impersonation=False,
            legitimate_domains=[],
            email_sender_domain=sender_domain
        )


# ============================================================================
# OCR Text Extractor
# ============================================================================

class OCRTextExtractor:
    """Extract text from images using Tesseract OCR"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.enabled = TESSERACT_AVAILABLE
        
        if self.enabled:
            logger.info("OCR text extraction enabled (Tesseract)")
        else:
            logger.warning("Tesseract not available - OCR disabled")
    
    def extract_text(self, image_data: bytes) -> Optional[str]:
        """Extract text from image"""
        if not self.enabled:
            return None
        
        try:
            image = Image.open(BytesIO(image_data))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text
            text = pytesseract.image_to_string(image)
            
            return text.strip() if text else None
            
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            return None


# ============================================================================
# Main Image Scanner
# ============================================================================

class ImageScanner:
    """
    Complete image scanning and analysis
    
    Combines:
    - QR code detection (quishing)
    - Logo detection (brand impersonation)
    - OCR (text extraction)
    - Screenshot detection
    - Threat analysis
    """
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Initialize sub-scanners
        self.qr_scanner = QRCodeScanner(config.get('qr_code', {}))
        self.logo_detector = LogoDetector(config.get('logo_detection', {}))
        self.ocr_extractor = OCRTextExtractor(config.get('ocr', {}))
        
        logger.info("Image Scanner initialized")
    
    def scan_image(
        self, 
        image_data: bytes, 
        sender_domain: Optional[str] = None
    ) -> ImageAnalysisResult:
        """
        Complete image analysis
        
        Args:
            image_data: Image bytes
            sender_domain: Email sender domain (for impersonation check)
            
        Returns:
            Complete analysis result
        """
        indicators = []
        threat_score = 0.0
        
        # 1. QR Code Detection
        qr_codes = self.qr_scanner.scan_image(image_data)
        has_qr_code = len(qr_codes) > 0
        
        if has_qr_code:
            indicators.append(f"Contains {len(qr_codes)} QR code(s)")
            
            # Analyze QR codes for threats
            for qr in qr_codes:
                analysis = self.qr_scanner.analyze_qr_code(qr)
                if analysis['is_suspicious']:
                    threat_score = max(threat_score, analysis['threat_score'])
                    indicators.extend(analysis['indicators'])
        
        # 2. Logo Detection
        logo_result = self.logo_detector.detect_logo(image_data, sender_domain)
        has_logo = logo_result.detected
        
        if logo_result.is_impersonation:
            indicators.append(
                f"Logo impersonation: {logo_result.brand} logo detected "
                f"but sender is {sender_domain}"
            )
            threat_score = max(threat_score, 0.9)
        
        # 3. OCR Text Extraction
        extracted_text = self.ocr_extractor.extract_text(image_data)
        has_text = bool(extracted_text and len(extracted_text) > 10)
        
        if has_text and extracted_text:
            # Check for suspicious keywords in text
            suspicious_keywords = [
                'verify', 'suspended', 'click here', 'urgent',
                'account', 'password', 'login', 'confirm'
            ]
            text_lower = extracted_text.lower()
            matches = sum(1 for kw in suspicious_keywords if kw in text_lower)
            
            if matches >= 3:
                indicators.append(f"Suspicious text content ({matches} keywords)")
                threat_score = max(threat_score, 0.6)
        
        # 4. Screenshot Detection (heuristic)
        is_screenshot = self._detect_screenshot(image_data, extracted_text)
        if is_screenshot:
            indicators.append("Appears to be a screenshot")
            threat_score = max(threat_score, 0.4)
        
        # Overall threat assessment
        is_suspicious = threat_score > 0.5
        
        return ImageAnalysisResult(
            has_qr_code=has_qr_code,
            qr_codes=qr_codes,
            has_logo=has_logo,
            logo_detection=logo_result if has_logo else None,
            has_text=has_text,
            extracted_text=extracted_text,
            is_screenshot=is_screenshot,
            is_suspicious=is_suspicious,
            threat_score=threat_score,
            indicators=indicators
        )
    
    def _detect_screenshot(
        self, 
        image_data: bytes, 
        extracted_text: Optional[str]
    ) -> bool:
        """
        Detect if image is likely a screenshot
        
        Heuristics:
        - Contains UI elements (buttons, forms)
        - Has typical screenshot dimensions
        - Contains browser/OS UI text
        """
        try:
            image = Image.open(BytesIO(image_data))
            width, height = image.size
            
            # Check aspect ratio (screenshots often match common screen ratios)
            aspect_ratio = width / height
            common_ratios = [16/9, 16/10, 4/3, 21/9]
            matches_common_ratio = any(
                abs(aspect_ratio - ratio) < 0.1 
                for ratio in common_ratios
            )
            
            # Check for UI keywords in OCR text
            if extracted_text:
                ui_keywords = [
                    'submit', 'login', 'sign in', 'continue',
                    'cancel', 'ok', 'close', 'menu', 'file', 'edit'
                ]
                text_lower = extracted_text.lower()
                has_ui_keywords = any(kw in text_lower for kw in ui_keywords)
            else:
                has_ui_keywords = False
            
            return matches_common_ratio and has_ui_keywords
            
        except Exception as e:
            logger.error(f"Screenshot detection error: {e}")
            return False


# ============================================================================
# Example Usage
# ============================================================================

def main():
    """Example usage"""
    
    config = {
        'qr_code': {
            'use_ai_detection': True
        },
        'logo_detection': {},
        'ocr': {}
    }
    
    scanner = ImageScanner(config)
    
    # Example: Scan an image
    print("Image Scanner initialized and ready!")
    print(f"QR Code Detection: {'✓' if PYZBAR_AVAILABLE or QREADER_AVAILABLE else '✗'}")
    print(f"AI QR Detection: {'✓' if QREADER_AVAILABLE else '✗'}")
    print(f"Logo Detection: {'✓' if CLIP_AVAILABLE else '✗'}")
    print(f"OCR: {'✓' if TESSERACT_AVAILABLE else '✗'}")


if __name__ == "__main__":
    main()





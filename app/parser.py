import re
import logging

logger = logging.getLogger(__name__)

class CardParser:
    """Parseur pour identifier les champs dans le texte OCR"""
    
    def __init__(self):
        # Patterns email
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Patterns téléphone
        self.phone_patterns = [
            r'(?:\+212|00212)[5-7]\d{8}',           # Maroc +212
            r'(?:\+33|0033)[1-9]\d{8}',             # France +33
            r'0[5-7]\d{8}',                          # Maroc 0X
            r'0[1-9]\d{8}',                          # France 0X
            r'\+[0-9]{1,3}[0-9]{9,10}',              # Autres internationaux
            r'[05-7]\d{8,9}',                        # Format simple
        ]
        
        # Mots-clés pour société
        self.company_keywords = [
            'SARL', 'SA', 'SAS', 'EURL', 'INC', 'LTD', 'CORP', 
            'COMPANY', 'SOCIETE', 'GROUP', 'ENTERPRISE', 'ENTREPRISE',
            'GMBH', 'LLC', 'CO', 'CORPORATION', 'ASSOCIATION'
        ]
        
        # Mots-clés pour titre
        self.title_keywords = [
            'DIRECTEUR', 'MANAGER', 'PRESIDENT', 'CEO', 'CTO', 'CFO',
            'CHEF', 'RESPONSABLE', 'CHARGE', 'CONSULTANT', 'INGENIEUR',
            'DEVELOPPEUR', 'ARCHITECTE', 'FONDATEUR', 'CO-FONDATEUR',
            'DIRECTOR', 'HEAD', 'LEAD', 'SENIOR', 'JUNIOR'
        ]
        
        # Stop words (mots à ignorer pour le nom)
        self.stop_words = ['TEL', 'FAX', 'EMAIL', 'WEB', 'WWW', 'HTTP', 'HTTPS']
        
    def parse(self, text):
        """
        Parse le texte pour extraire les champs
        
        Args:
            text: texte extrait par OCR
            
        Returns:
            dict avec les champs identifiés
        """
        data = {
            'nom': None,
            'prenom': None,
            'telephone': None,
            'email': None,
            'societe': None,
            'titre': None
        }
        
        if not text:
            logger.warning("Texte vide à parser")
            return data
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        logger.info(f"Parsing de {len(lines)} lignes")
        
        # 1. Trouver EMAIL
        for line in lines:
            emails = re.findall(self.email_pattern, line, re.IGNORECASE)
            if emails:
                data['email'] = emails[0].lower()
                logger.info(f"Email trouvé: {data['email']}")
                break
        
        # 2. Trouver TELEPHONE
        for line in lines:
            for pattern in self.phone_patterns:
                phones = re.findall(pattern, line)
                if phones:
                    # Nettoyer le numéro
                    phone = self._clean_phone(phones[0])
                    if phone:
                        data['telephone'] = phone
                        logger.info(f"Téléphone trouvé: {data['telephone']}")
                        break
            if data['telephone']:
                break
        
        # 3. Trouver NOM/PRENOM (généralement première ligne)
        if lines:
            potential_name = lines[0]
            # Vérifier que ce n'est pas un email ou téléphone
            if (not re.search(self.email_pattern, potential_name) and
                not any(re.search(p, potential_name) for p in self.phone_patterns) and
                not any(stop in potential_name.upper() for stop in self.stop_words)):
                
                name_parts = potential_name.split()
                if len(name_parts) == 2:
                    data['prenom'] = name_parts[0]
                    data['nom'] = name_parts[1]
                    logger.info(f"Nom complet trouvé: {data['prenom']} {data['nom']}")
                elif len(name_parts) == 1:
                    data['nom'] = name_parts[0]
                    logger.info(f"Nom trouvé: {data['nom']}")
                elif len(name_parts) == 3:  # Prénom + Nom + Nom
                    data['prenom'] = name_parts[0]
                    data['nom'] = f"{name_parts[1]} {name_parts[2]}"
                    logger.info(f"Nom composé trouvé: {data['nom']}")
        
        # 4. Trouver SOCIETE
        for i, line in enumerate(lines):
            # Ignorer la première ligne (nom)
            if i == 0:
                continue
                
            # Vérifier si la ligne contient des mots-clés société
            line_upper = line.upper()
            for keyword in self.company_keywords:
                if keyword in line_upper:
                    data['societe'] = line
                    logger.info(f"Société trouvée: {data['societe']}")
                    break
            
            # Si pas de mot-clé mais ligne courte et pas email/tel
            if not data['societe'] and len(line.split()) <= 4:
                if (not re.search(self.email_pattern, line) and
                    not any(re.search(p, line) for p in self.phone_patterns)):
                    data['societe'] = line
                    logger.info(f"Société probable trouvée: {data['societe']}")
                    break
            
            if data['societe']:
                break
        
        # 5. Trouver TITRE
        for i, line in enumerate(lines):
            # Chercher après le nom
            if i > 0 and i < 4:  # Regarder lignes 2-4
                line_upper = line.upper()
                for keyword in self.title_keywords:
                    if keyword in line_upper:
                        data['titre'] = line
                        logger.info(f"Titre trouvé: {data['titre']}")
                        break
                if data['titre']:
                    break
        
        return data
    
    def _clean_phone(self, phone):
        """Nettoie le numéro de téléphone"""
        # Enlever tous les caractères non digits sauf +
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Formater si possible
        if cleaned.startswith('+212') and len(cleaned) == 13:
            return cleaned
        elif cleaned.startswith('0') and len(cleaned) == 10:
            return cleaned
        elif len(cleaned) == 9:  # Ajouter 0 si besoin
            return '0' + cleaned
        
        return cleaned
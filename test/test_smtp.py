"""
Script de test de connexion SMTP
Permet de diagnostiquer les problèmes de connexion email
"""

import socket
import sys


def test_smtp_connection(host, port):
    """Tester la connexion SMTP basique"""
    print(f"📡 Test de connexion à {host}:{port}...")

    try:
        # Créer un socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)

        # Essayer de se connecter
        result = sock.connect_ex((host, port))

        if result == 0:
            print(f"   ✅ Connexion réussie à {host}:{port}")
            print(f"   → Le serveur est accessible")
            return True
        else:
            print(f"   ❌ Impossible de se connecter à {host}:{port}")
            print(f"   → Code d'erreur : {result}")
            return False

    except socket.timeout:
        print(f"   ❌ Timeout lors de la connexion à {host}:{port}")
        print(f"   → Le serveur ne répond pas dans les 10 secondes")
        return False
    except socket.gaierror as e:
        print(f"   ❌ Erreur de résolution DNS : {e}")
        print(f"   → Le nom de domaine {host} est introuvable")
        return False
    except Exception as e:
        print(f"   ❌ Erreur : {e}")
        return False
    finally:
        try:
            sock.close()
        except Exception:
            pass
    print()


def test_dns_resolution(host):
    """Tester la résolution DNS"""
    print(f"🔍 Test de résolution DNS pour {host}...")

    try:
        ip = socket.gethostbyname(host)
        print(f"   ✅ {host} résolu en {ip}")
        return True
    except socket.gaierror as e:
        print(f"   ❌ Impossible de résoudre {host}")
        print(f"   → Erreur : {e}")
        return False
    print()


def main():
    """Fonction principale"""

    print()
    print(
        "╔════════════════════════════════════════════════════════════════════════════╗"
    )
    print(
        "║                                                                            ║"
    )
    print(
        "║                    🔧 TEST DE CONNECTIVITÉ SMTP 🔧                         ║"
    )
    print(
        "║                                                                            ║"
    )
    print(
        "╚════════════════════════════════════════════════════════════════════════════╝"
    )
    print()

    # Liste des serveurs à tester
    # 👉 On utilise ici smtp.office365.com (pas ton adresse mail + .local)
    servers_to_test = [
        # Office 365 (configuration classique)
        ("smtp.office365.com", 587, "Office 365 - STARTTLS (recommandé)"),
        ("smtp.office365.com", 25, "Office 365 - Port 25 (si autorisé)"),
        ("smtp.office365.com", 465, "Office 365 - SSL (legacy)"),
        # Exemple de serveur SMTP interne (à demander à la DSI)
        # Remplacer 'relay.hopital-foch.local' par le vrai nom fourni par l'IT
        # ("relay.hopital-foch.local", 25, "SMTP interne Hôpital Foch - Port 25"),
    ]

    results = []

    # Test de résolution DNS d'abord
    print("=" * 80)
    print("ÉTAPE 1 : TEST DE RÉSOLUTION DNS")
    print("=" * 80)
    print()

    unique_hosts = list(set([host for host, _, _ in servers_to_test]))
    for host in unique_hosts:
        dns_ok = test_dns_resolution(host)
        print()

    # Test de connexion pour chaque serveur
    print("=" * 80)
    print("ÉTAPE 2 : TEST DE CONNEXION AUX PORTS SMTP")
    print("=" * 80)
    print()

    for host, port, description in servers_to_test:
        print(f"📋 {description}")
        success = test_smtp_connection(host, port)
        results.append((host, port, description, success))
        print()

    # Résumé
    print("=" * 80)
    print("RÉSUMÉ DES TESTS")
    print("=" * 80)
    print()

    success_count = sum(1 for _, _, _, success in results if success)
    total_count = len(results)

    print(f"✅ Tests réussis : {success_count}/{total_count}")
    print()

    if success_count == 0:
        print("❌ AUCUN serveur SMTP accessible")
        print()
        print("🔍 Diagnostic possible :")
        print("   1. Le firewall bloque TOUTES les connexions SMTP sortantes")
        print("   2. Vous êtes sur un réseau hospitalier très restreint")
        print("   3. Un proxy ou un relais SMTP interne est requis")
        print()
        print("✅ Solutions recommandées :")
        print("   1. Contacter le service IT de l'hôpital")
        print("   2. Demander l'adresse du serveur SMTP/Exchange INTERNE")
        print("      (ex : relay.hopital-foch.local ou un autre nom fourni par l'IT)")
        print("   3. Demander si un proxy est nécessaire pour sortir sur Internet")
        print("   4. En attendant : envoyer les rapports manuellement par Outlook")
        print()

    elif success_count < total_count:
        print("⚠️  CERTAINS serveurs sont accessibles")
        print()
        print("✅ Serveurs accessibles :")
        for host, port, desc, success in results:
            if success:
                print(f"   ✓ {desc} ({host}:{port})")
        print()
        print("❌ Serveurs non accessibles :")
        for host, port, desc, success in results:
            if not success:
                print(f"   ✗ {desc} ({host}:{port})")
        print()
        print("✅ Recommandation :")
        print("   → Utiliser un des serveurs accessibles dans votre fichier .env")
        print()
    else:
        print("✅ TOUS les serveurs sont accessibles")
        print()
        print("🎉 Votre réseau permet les connexions SMTP sortantes !")
        print()
        print("🔍 Si l'envoi d'email échoue quand même, vérifier :")
        print("   1. Les identifiants SMTP dans .env (user/password)")
        print("   2. L'authentification Office 365 (MFA, mot de passe d'app)")
        print("   3. Les logs d'erreur pour plus de détails")
        print()

    # Informations additionnelles
    print("=" * 80)
    print("INFORMATIONS COMPLÉMENTAIRES")
    print("=" * 80)
    print()

    print("📋 Pour configurer le serveur SMTP dans .env :")
    print()
    for host, port, desc, success in results:
        if success:
            print(f"Option : {desc}")
            print(f"SMTP_HOST={host}")
            print(f"SMTP_PORT={port}")
            print()

    print("=" * 80)
    print("PROCHAINES ÉTAPES")
    print("=" * 80)
    print()

    if success_count > 0:
        print(
            "1. Choisir un serveur accessible ci-dessus (idéalement smtp.office365.com:587)"
        )
        print("2. Modifier votre fichier .env avec les bons paramètres")
        print(
            "3. Vérifier vos identifiants SMTP (user = votre email, password = mot de passe / mot de passe d'app)"
        )
        print("4. Relancer le test d'email : python test/test_ppt_email.py")
    else:
        print("1. Contacter le service IT : helpdesk@hopital-foch.com")
        print("2. Demander :")
        print(
            "   - Adresse du serveur SMTP interne (nom EXACT, pas votre mail + .local)"
        )
        print("   - Port à utiliser (25, 587, ou 465)")
        print("   - Si un proxy est nécessaire")
        print("3. En attendant : utiliser Outlook pour envoyer manuellement")
        print()

    print()
    print("📧 Support : s.ben-yahia@hopital-foch.com")
    print()

    return 0 if success_count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())

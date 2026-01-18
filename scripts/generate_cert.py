
import os
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from pathlib import Path

def generate_self_signed_cert():
    base_dir = Path(__file__).resolve().parent.parent
    cert_dir = base_dir / "Certifica"
    cert_dir.mkdir(exist_ok=True)
    
    key_path = cert_dir / "key.pem"
    cert_path = cert_dir / "cert.pem"

    # Generate Key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Generate Cert
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"TR"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Istanbul"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"Sisli"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"EXFIN OPS"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        # 10 Years Validity
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
        critical=False,
    ).sign(key, hashes.SHA256())

    # Write Key
    with open(key_path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    # Write Cert
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"SUCCESS: Certificate generated at {cert_path}")
    return str(cert_path), str(key_path)

if __name__ == "__main__":
    try:
        generate_self_signed_cert()
    except Exception as e:
        print(f"ERROR: {e}")

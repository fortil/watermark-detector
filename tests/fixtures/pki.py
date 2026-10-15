"""Throwaway PKI used to sign test assets. Not trusted by anything."""
from __future__ import annotations

import datetime
from dataclasses import dataclass

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


@dataclass(frozen=True)
class TestPki:
    __test__ = False  # not a pytest class

    chain_pem: bytes
    root_pem: bytes
    intermediate_pem: bytes
    key_pem: bytes
    chain_der: tuple[bytes, bytes]


def _name(org: str, cn: str) -> x509.Name:
    return x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, org),
            x509.NameAttribute(NameOID.COMMON_NAME, cn),
        ]
    )


def make_chain(org: str, leaf_cn: str) -> TestPki:
    start = datetime.datetime(2025, 12, 31, tzinfo=datetime.timezone.utc)
    end = start + datetime.timedelta(days=3650)

    def build(subject, issuer, pub, signer_key, *, ca, path_len, leaf, issuer_pub):
        b = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(pub)
            .serial_number(x509.random_serial_number())
            .not_valid_before(start)
            .not_valid_after(end)
            .add_extension(
                x509.BasicConstraints(ca=ca, path_length=path_len), critical=True
            )
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(pub), critical=False)
        )
        if issuer_pub is not None:
            b = b.add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_public_key(issuer_pub),
                critical=False,
            )
        if leaf:
            b = b.add_extension(
                x509.KeyUsage(
                    digital_signature=True, content_commitment=False,
                    key_encipherment=False, data_encipherment=False,
                    key_agreement=False, key_cert_sign=False, crl_sign=False,
                    encipher_only=False, decipher_only=False,
                ),
                critical=True,
            ).add_extension(
                x509.ExtendedKeyUsage([ExtendedKeyUsageOID.EMAIL_PROTECTION]),
                critical=False,
            )
        else:
            b = b.add_extension(
                x509.KeyUsage(
                    digital_signature=False, content_commitment=False,
                    key_encipherment=False, data_encipherment=False,
                    key_agreement=False, key_cert_sign=True, crl_sign=True,
                    encipher_only=False, decipher_only=False,
                ),
                critical=True,
            )
        return b.sign(signer_key, hashes.SHA256())

    root_key = ec.generate_private_key(ec.SECP256R1())
    int_key = ec.generate_private_key(ec.SECP256R1())
    leaf_key = ec.generate_private_key(ec.SECP256R1())
    root_name = _name(org, f"{org} Test Root")
    int_name = _name(org, f"{org} Test Intermediate")
    leaf_name = _name(org, leaf_cn)

    root = build(root_name, root_name, root_key.public_key(), root_key,
                 ca=True, path_len=1, leaf=False, issuer_pub=None)
    inter = build(int_name, root_name, int_key.public_key(), root_key,
                  ca=True, path_len=0, leaf=False, issuer_pub=root_key.public_key())
    leaf = build(leaf_name, int_name, leaf_key.public_key(), int_key,
                 ca=False, path_len=None, leaf=True, issuer_pub=int_key.public_key())

    pem = serialization.Encoding.PEM
    der = serialization.Encoding.DER
    return TestPki(
        chain_pem=leaf.public_bytes(pem) + inter.public_bytes(pem),
        root_pem=root.public_bytes(pem),
        intermediate_pem=inter.public_bytes(pem),
        key_pem=leaf_key.private_bytes(
            pem, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
        ),
        chain_der=(leaf.public_bytes(der), inter.public_bytes(der)),
    )

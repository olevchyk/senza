from datetime import datetime, timezone

from typing import Optional, Dict, Any, Union, Iterator
import boto3


class IAMServerCertificate:
    """
    Server certificate stored in IAM.

    See:
    http://boto3.readthedocs.io/en/latest/reference/services/iam.html#IAM.Client.get_server_certificate
    """

    def __init__(self,
                 metadata: Dict[str, Union[str, datetime]],
                 certificate_body: str,
                 certificate_chain: str):

        self.metadata = metadata
        self.certificate_body = certificate_body
        self.certificate_chain = certificate_chain

        # metadata properties
        self.name = metadata['ServerCertificateName']  # type: str
        self.arn = metadata['Arn']  # type: str
        self.expiration = metadata['Expiration']  # type: datetime
        self.path = metadata['Path']  # type: str
        self.certificate_id = metadata['ServerCertificateId']  # type: str
        self.upload_date = metadata['UploadDate']  # type: datetime

    def __lt__(self, other: "IAMServerCertificate"):
        return self.upload_date < other.upload_date

    def __eq__(self, other: "IAMServerCertificate"):
        return self.arn == other.arn

    def __repr__(self):
        return "<IAMServerCertificate: {name}>".format_map(vars(self))

    @classmethod
    def from_boto_dict(cls,
                       server_certificate: Dict[str, Any]) -> "IAMServerCertificate":

        metadata = server_certificate['ServerCertificateMetadata']
        certificate_body = server_certificate['CertificateBody']
        certificate_chain = server_certificate['CertificateChain']

        return cls(metadata, certificate_body, certificate_chain)

    @classmethod
    def from_boto_server_certificate(cls, server_certificate) -> "IAMServerCertificate":
        """
        Converts an ServerCertificate as returned by server_certificates.all()
        """
        metadata = server_certificate.server_certificate_metadata
        certificate_body = server_certificate.certificate_body
        certificate_chain = server_certificate.certificate_chain

        return cls(metadata, certificate_body, certificate_chain)

    @classmethod
    def get_by_name(cls, name: str) -> "IAMServerCertificate":
        """
        Get IAMServerCertificate using the name of the server certificate
        """
        client = boto3.client('iam')
        response = client.get_server_certificate(ServerCertificateName=name)
        server_certificate = response['ServerCertificate']

        return cls.from_boto_dict(server_certificate)

    @staticmethod
    def arn_is_server_certificate(arn: Optional[str] = None):
        """
        Checks if the Amazon Resource Name (ARN) refers to an iam
        server certificate.

        See:
        http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html
        """
        if arn is None:
            return False
        else:
            return (arn.startswith("arn:aws:iam:") and
                    'server-certificate' in arn)

    def is_valid(self, when: Optional[datetime]=None) -> bool:
        """
        Checks if the certificate is still valid
        """
        when = when if when is not None else datetime.now(timezone.utc)

        return when < self.expiration


class IAM:

    @staticmethod
    def get_certificates(valid_only: bool=True,
                         name: Optional[str] = None) -> Iterator[IAMServerCertificate]:
        resource = boto3.resource('iam')

        for server_certificate in resource.server_certificates.all():
            certificate = IAMServerCertificate.from_boto_server_certificate(server_certificate)

            if name is not None and certificate.name != name:
                continue

            if valid_only and not certificate.is_valid():
                continue

            yield certificate

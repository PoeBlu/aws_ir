import uuid

"""Class to create the cases s3 bucket for asset storage"""


class CaseBucket(object):
    def __init__(self, case_number, region, client, resource):
        self.region = region
        self.case_number = case_number
        self.client = client
        self.s3 = resource.connect()
        self.bucket = self.find_or_create_by()

    def find_or_create_by(self):
        bucket = self._locate_bucket()
        if bucket is None:
            self.bucket_name = self._generate_name()
            bucket = self._create_s3_bucket()
            self._set_acls(self.bucket_name)
            self._set_tags(self.bucket_name)
            self._set_versioning(self.bucket_name)
        return bucket

    def cleanup_empty_buckets(self):
        buckets = self.client.list_buckets()
        for bucket in buckets['Buckets']:
            if 'cloud-response' in str(bucket['Name']):
                try:
                    self.client.delete_bucket(Bucket=bucket['Name'])
                    print(bucket['Name'])
                except Exception:
                    pass

    def _generate_name(self):
        return 'cloud-response-' + str(uuid.uuid4()).replace('-', '')

    def _create_s3_bucket(self):
        return (
            self.s3.create_bucket(Bucket=self.bucket_name)
            if self.region == 'us-east-1'
            else self.s3.create_bucket(
                Bucket=self.bucket_name,
                CreateBucketConfiguration={'LocationConstraint': self.region},
            )
        )

    def _set_acls(self, bucket_name):
        self.s3.BucketAcl(bucket_name).put(ACL='bucket-owner-full-control')

    def _set_tags(self, bucket_name):
        self.client.put_bucket_tagging(
            Bucket=bucket_name,
            Tagging=dict(
                TagSet=[
                    dict(
                        Key='cr-case-number',
                        Value=self.case_number
                    )
                ]
            )
        )

    def _set_versioning(self, bucket_name):
        self.client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration=dict(
                MFADelete='Disabled',
                Status='Enabled'
            )
        )

    def _locate_bucket(self):
        buckets = self.s3.buckets.all()
        for bucket in buckets:
            if bucket.name.startswith("cloud-response-"):
                tags = self._get_bucket_tags(bucket.name)
                return bucket if self._check_tags(tags) else None

    def _get_bucket_tags(self, bucket):
        try:
            s3 = self.client
            response = s3.get_bucket_tagging(
                Bucket=bucket,
            )
        except Exception:
            response = None
        return response

    def _check_tags(self, tag_object):
        if tag_object is None:
            return False
        elif tag_object.get('TagSet', None) is not None:
            for tag in tag_object['TagSet']:
                return tag['Value'] == self.case_number
        else:
            return False

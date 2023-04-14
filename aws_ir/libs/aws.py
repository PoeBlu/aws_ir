class AmazonWebServices(object):
    def __init__(self, client):
        self.client = client
        self.regions = self._get_regions()
        self.availability_zones = self._get_availability_zones()

    def _get_regions(self):
        """Use the provided AWS Client to iterate over the regions and store them."""

        regions = self.client.connect().describe_regions()
        return [region['RegionName'] for region in regions['Regions']]

    def _get_availability_zones(self):
        """Use the provided AWS Client to iterate over the azs and store them"""

        availZones = []
        for region in self.regions:
            self.client.region = region
            client = self.client.connect()
            zones = client.describe_availability_zones()['AvailabilityZones']
            availZones.extend(
                zone['ZoneName'] for zone in zones if zone['State'] == 'available'
            )
        return availZones

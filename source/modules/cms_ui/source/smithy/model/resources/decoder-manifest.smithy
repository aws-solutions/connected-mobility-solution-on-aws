$version: "2.0"
namespace com.cms.fleetmanagement

resource DecoderManifest {
    identifiers: {
        name: ResourceName
    }
    list: ListDecoderManifests
}

structure DecoderManifestItem for DecoderManifest {
    @required
    arn: ARN

    @required
    name: ResourceName

    @required
    modelManifestArn: ARN
}

list DecoderManifestItems {
    member: DecoderManifestItem
}

@http(code: 200, method: "GET", uri: "/decoder-manifest")
@readonly
operation ListDecoderManifests {
    output := {
      decoderManifests: DecoderManifestItems
    }
}

$version: "2.0"

// The MemberShouldReferenceResource validator checks globally whether a member name
// is uniquely associated with a resource. Hence, this shows a warning for members
// with common names such as 'name' which is not unique for every resource.
metadata suppressions = [
    {
        id: "MemberShouldReferenceResource"
        namespace: "*"
    }
]

namespace com.cms.fleetmanagement

use aws.apigateway#integration
use aws.apigateway#authorizer
use aws.apigateway#authorizers
use aws.protocols#restJson1
use smithy.framework#ValidationException

@title("CMS Fleet Management Service")
@aws.apigateway#integration(
    type: "aws_proxy",
    httpMethod: "POST",
    uri: "arn:${AWS::Partition}:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${LambdaFunction.Arn}/invocations",
    passThroughBehavior: "never",
    timeoutInMillis: 29000,
)
@cors(
  origin: "*",
  additionalAllowedHeaders: ["*"],
)
@httpApiKeyAuth(name: "Authorization", in: "header")
@authorizer("LambdaOAuthAuthorizer")
@authorizers(
    LambdaOAuthAuthorizer : {
      scheme: "smithy.api#httpApiKeyAuth",
      type: "request",
      uri: "arn:${AWS::Partition}:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${AuthLambdaFunction.Arn}/invocations",
      identitySource: "method.request.header.Authorization",
      resultTtlInSeconds: 60
})
@restJson1
service FleetManagement {
    version: "2024-08-23"
    resources: [Fleet, Campaign, Vehicle, SignalCatalog, DecoderManifest]
    errors: [
        ValidationException
    ]
}

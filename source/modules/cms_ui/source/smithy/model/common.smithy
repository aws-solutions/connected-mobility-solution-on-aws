$version: "2.0"
namespace com.cms.fleetmanagement

structure Tag {
  @required
  Key: String

  @required
  Value: String
}

list Tags {
    member: Tag
}

@pattern("(^$)|(arn:aws:[a-z-]+:[a-z0-9-]+:\\d{12}:[a-z-]+[:/][a-zA-Z0-9/_+=.@-]+)")
string ARN

@pattern("^[a-zA-Z\\d]+[a-zA-Z\\d\\-_:]*")
@length(min: 1)
string ResourceName

@length(min: 1)
string NonEmptyString

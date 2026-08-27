# delta-protocol

Runtime-neutral authoritative schemas, media types, action IDs and exact byte fixtures.

This component contains data contracts only. It cannot import Python training code, native C++
code, Java classes, transport libraries or framework object layouts. JSON objects are hashed only
after the canonical UTF-8 encoding declared by the fixtures. Tensor vectors use the documented
safe tensor envelope and never pickle.

The registry binds every contract to formal semantics
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.

Feature 003 adds `delta-canonical-binary-v1`: an explicit envelope and typed-value codec with
immutable type codes and hash domains. Its valid, invalid and cross-language fixtures are data
contracts only; the Python verifier is fixture/evidence tooling and does not implement validator
state transitions.

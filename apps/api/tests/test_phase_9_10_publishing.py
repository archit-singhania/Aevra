import httpx

from aevra_api.publishing.contracts import (
    LinkedInPublisher,
    MockSocialPublisher,
    PublishRequest,
    PublishStatus,
)


def test_mock_publisher_is_idempotent_and_replay_safe() -> None:
    publisher = MockSocialPublisher()
    request = PublishRequest("campaign-1-v1-linkedin", "urn:li:organization:1", "Hello Aevra")
    first = publisher.publish(request, access_token="opaque-ref")
    second = publisher.publish(request, access_token="opaque-ref")
    assert first.status == PublishStatus.PUBLISHED
    assert second.status == PublishStatus.ALREADY_PUBLISHED
    assert first.external_post_id == second.external_post_id


def test_linkedin_publisher_publishes_and_verifies_without_leaking_token() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("ugcPosts"):
            return httpx.Response(201, headers={"x-restli-id": "urn:li:share:123"})
        return httpx.Response(200, json={"id": "urn:li:share:123"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    publisher = LinkedInPublisher(base_url="https://sandbox.linkedin.test", client=client)
    request = PublishRequest("key-12345678", "urn:li:organization:1", "A grounded launch")
    published = publisher.publish(request, access_token="secret-token")
    verified = publisher.verify("urn:li:share:123", access_token="secret-token")
    assert published.status == PublishStatus.PUBLISHED
    assert verified.raw_metadata["verified"] is True
    assert all("secret-token" not in str(call.headers) for call in calls)
    assert calls[0].headers["Authorization"] == "Bearer secret-token"


def test_linkedin_rate_limit_is_retryable() -> None:
    client = httpx.Client(transport=httpx.MockTransport(lambda _request: httpx.Response(429)))
    publisher = LinkedInPublisher(client=client)
    try:
        publisher.publish(
            PublishRequest("key-87654321", "urn:li:organization:1", "Retry me"),
            access_token="token",
        )
    except Exception as error:
        assert error.retryable is True
    else:
        raise AssertionError("rate limiting must fail with a retryable publisher error")

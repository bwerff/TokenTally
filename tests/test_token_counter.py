import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import importlib.util
import token_tally as tt
import token_tally.token_counter as tc


def _expected_openai(text: str) -> int:
    if importlib.util.find_spec("tiktoken"):
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    return len(tc._regex_split(text))


def _expected_anthropic(text: str) -> int:
    if importlib.util.find_spec("anthropic"):
        from anthropic import count_tokens as anthropic_count_tokens

        return anthropic_count_tokens(text)
    return len(tc._regex_split(text))


def _expected_cohere(text: str) -> int:
    return len(tc._regex_split(text))


def test_count_tokens():
    assert tt.count_openai_tokens("hello world!") == _expected_openai("hello world!")
    assert tt.count_anthropic_tokens("chatGPT") == _expected_anthropic("chatGPT")
    assert tt.count_cohere_tokens("hello") == _expected_cohere("hello")
    assert tt.count_local_tokens("one two three") == 3
    assert tt.count_tokens("openai", "foo bar") == _expected_openai("foo bar")
    assert tt.count_tokens("anthropic", "foo bar baz") == _expected_anthropic(
        "foo bar baz"
    )
    assert tt.count_tokens("cohere", "foo bar baz qux") == _expected_cohere(
        "foo bar baz qux"
    )
    assert tt.count_tokens("local", "a b c d") == 4


def test_parse_dcgm_gpu_minutes():
    lines = [
        "timestamp,gpu_util",
        "0,50",
        "60,100",
        "120,0",
    ]
    result = tt.parse_dcgm_gpu_minutes(lines)
    assert abs(result - 1.5) < 1e-6

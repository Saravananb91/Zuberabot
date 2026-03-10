import sys
import zuberabot

print("SYS.PATH:")
for p in sys.path:
    print(f" - {p}")

print(f"\nNANOBOT LOADED FROM: {zuberabot.__file__}")

try:
    from zuberabot.providers.litellm_provider import LiteLLMProvider
    print("\nLITELLM PROVIDER STILL EXISTS!")
except ImportError:
    print("\nLITELLM PROVIDER GONE (SUCCESS!)")

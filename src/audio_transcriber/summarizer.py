import subprocess

PROMPT = "Summarize this German transcript concisely in German"

class ClaudeSummarizer:
    """Real Claude summarizer implementation."""
    def summarize(self, text: str) -> None:
        """Summarize transcript using Claude."""
        try:
            result = subprocess.run(
                ["claude", "-"],
                input=f"{PROMPT}: \n\n{text}",
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.stdout:
                print("\n📝 Summary:")
                print(result.stdout)
        except Exception as e:
            print(f"Summary error: {e}")
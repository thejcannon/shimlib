import httpx
import typer
import os

app = typer.Typer()


@app.command()
def update_pipeline(pipeline_file: str):
    token = os.environ.get("BK_TOKEN")
    if not token:
        token = typer.prompt("Enter your BuildKite token", hide_input=True)
        if not token:
            typer.echo("Error: BuildKite token is required.")
            return
        return

    base_url = "https://api.buildkite.com/v2"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # Read pipeline configuration from file
        with open(pipeline_file, "r") as file:
            pipeline_config = file.read()

        url = f"{base_url}/organizations/thejcannon/pipelines/test"
        resp = httpx.patch(
            url, headers=headers, json={"configuration": pipeline_config}
        ).raise_for_status()
        typer.echo("Pipeline 'test' updated successfully.")
        typer.echo(resp.json())
    except FileNotFoundError:
        typer.echo(f"Error: Pipeline file '{pipeline_file}' not found.")
    except httpx.HTTPStatusError as e:
        typer.echo(
            f"Error updating pipeline: HTTP {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        typer.echo(f"Error updating pipeline: {str(e)}")


def main():
    app()


if __name__ == "__main__":
    main()

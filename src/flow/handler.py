from azure.ai.projects.models import (
    AgentEventHandler,
    MessageDeltaChunk,
    MessageDeltaTextContent,
    RunStep,
    ThreadMessage,
    ThreadRun,
    MessageDeltaTextUrlCitationAnnotation,
)
from typing import Any

class MyEventHandler(AgentEventHandler):

    def on_message_delta(self, delta: "MessageDeltaChunk") -> None:
        print(f"Text delta received: {delta.text}")
        if delta.delta.content and isinstance(delta.delta.content[0], MessageDeltaTextContent):
            delta_text_content = delta.delta.content[0]
            if delta_text_content.text and delta_text_content.text.annotations:
                for delta_annotation in delta_text_content.text.annotations:
                    if isinstance(delta_annotation, MessageDeltaTextUrlCitationAnnotation):
                        print(
                            f"URL citation delta received: [{delta_annotation.url_citation.title}]({delta_annotation.url_citation.url})"
                        )

    def on_thread_message(self, message: "ThreadMessage") -> None:
        print(f"ThreadMessage created. ID: {message.id}, Status: {message.status}")

    def on_thread_run(self, run: "ThreadRun") -> None:
        print(f"ThreadRun status: {run.status}")

        if run.status == "failed":
            print(f"Run failed. Error: {run.last_error}")

    def on_run_step(self, step: "RunStep") -> None:
        print(f"RunStep type: {step.type}, Status: {step.status}")

    def on_error(self, data: str) -> None:
        print(f"An error occurred. Data: {data}")

    def on_done(self) -> None:
        print("Stream completed.")

    def on_unhandled_event(self, event_type: str, event_data: Any) -> None:
        print(f"Unhandled Event Type: {event_type}, Data: {event_data}")

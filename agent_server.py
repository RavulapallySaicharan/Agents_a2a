from python_a2a import A2AServer, skill, agent, run_server, TaskStatus, TaskState

@agent(
    name="Movie Review Agent",
    description="Provides movie reviews and opinions",
    version="1.0.0"
)
class MovieAgent(A2AServer):
    
    @skill(
        name="Movie Review",
        description="Get movie review or opinion",
        tags=["movie", "review"]
    )
    def get_movie_review(self, message):
        """Get movie review or opinion."""
        return f"I understand your opinion about the movie. Would you like to share more details about what you didn't like?"
    
    def handle_task(self, task):
        # Extract message from task
        message_data = task.message or {}
        content = message_data.get("content", {})
        text = content.get("text", "") if isinstance(content, dict) else ""
        
        # Get review and create response
        review_text = self.get_movie_review(text)
        task.artifacts = [{
            "parts": [{"type": "text", "text": review_text}]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        return task

# Run the server
if __name__ == "__main__":
    agent = MovieAgent()
    run_server(agent, port=5011) 
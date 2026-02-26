from ..utils.data_loader import get_videos_for_profile


def get_youtube_recommendations(
    goal: str,
    fitness_level: str,
    content_type: str = "both",
) -> dict:
    """Fetches relevant YouTube video recommendations based on user's goal and fitness level.

    Args:
        goal: The fitness goal - one of 'fat_loss', 'weight_gain', 'muscle_building', 'health_maintenance'.
        fitness_level: Current fitness level - one of 'beginner', 'intermediate', 'advanced'.
        content_type: Type of content to recommend - 'workout', 'diet', or 'both'. Defaults to 'both'.

    Returns:
        A dictionary containing a list of recommended YouTube videos with titles, URLs, and descriptions.
    """
    result = get_videos_for_profile(
        goal=goal,
        fitness_level=fitness_level,
        content_type=content_type,
    )
    return result

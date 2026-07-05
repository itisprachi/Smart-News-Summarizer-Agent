"""
Background job to generate and send daily newsletters to subscribed users.
"""

import logging

from services import auth_service, pipeline, email_service
from config import DEFAULT_MAX_ARTICLES, DEFAULT_LANGUAGE

logger = logging.getLogger(__name__)

async def run_daily_newsletter():
    """
    Executes the daily newsletter task.
    Iterates over all users, checks their subscriptions, fetches summaries,
    and sends them an email digest for each topic.
    """
    logger.info("Starting Daily Newsletter Job...")
    
    users = auth_service.get_all_users()
    
    for user in users:
        email = user.get("email")
        subscriptions = user.get("subscriptions", [])
        
        if not subscriptions:
            continue
            
        logger.info("Processing newsletter for %s (Topics: %d)", email, len(subscriptions))
        
        for topic in subscriptions:
            try:
                # Run the pipeline for the subscribed topic
                articles = await pipeline.run_pipeline(topic, DEFAULT_MAX_ARTICLES, DEFAULT_LANGUAGE)
                
                if articles:
                    # Send the email
                    # Convert ArticleResult objects to dicts for email_service
                    article_dicts = [a.dict() for a in articles]
                    await email_service.send_summary_email(email, topic, article_dicts)
                    logger.info("Successfully sent '%s' newsletter to %s", topic, email)
                else:
                    logger.info("No articles found for topic '%s' today.", topic)
            except Exception as exc:
                logger.error("Failed to process topic '%s' for user %s: %s", topic, email, exc)
                
    logger.info("Daily Newsletter Job completed.")

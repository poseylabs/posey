# Ideas/Brainstorm list:

## Multi-Source Location Context for Advanced Minion Intelligence

By extracting and providing multiple types of location context (e.g., query, user_profile, geolocation, browser_ip) in the orchestrator and passing them to all minions, we enable:
- More robust and accurate location-aware responses (e.g., weather, local search).
- The ability for minions to reason about user intent, travel, and context (e.g., user lives in NY, is in Denver, but asks about Seattle).
- Advanced features like multi-search: e.g., if the user is traveling, trigger parallel searches for weather at the destination, flight status, and food options at the layover location, all personalized by user preferences and context.
- Minions can use the prioritized location context to decide which location is most relevant for the current task, and can trigger additional helpful actions based on the full context.

**TODO:** Implement logic in minions to leverage the full location context for advanced, context-aware, and proactive assistance.

# Ideas list:





Current todo list for Posey AI:
- Add emoji support:
  - When gpt types emotions like *smiles* let's insert an emoji instead
- Add video generation

- Add Accountant minion
  - Manages information about current bank accounts, investments, and credit card debt
  - Able to make budgets, suggest investments, pay bills, manage sandboxed investment accounts, manage crypto wallet, etc
- Day trading minion
  - Manages information about current stock prices, market trends, etc
  - Able to buy and sell stocks, manage sandboxed investment accounts, etc
- Business Manager minion
  - Manages information about current business assets, liabilities, income, expenses, etc
  - Able to manage business finances, suggest investments, pay bills, manage sandboxed investment accounts, etc
- Add Personal Assistant minion
  - Manages information about current personal assets, liabilities, income, expenses, etc
  - Able to manage personal finances, suggest investments, pay bills, manage sandboxed investment accounts, etc
  - Manage schedules, reminders, etc
- Personal Health minion
  - Manages information about current nutrition goals, food inventory, recipes, etc
  - Able to track nutrition intake, suggest recipes, suggest supplements, etc
  - Plan & suggest exercise routines
  - Friendly reminders to excercise, take medication, drink water, brush teeth, floss, etc
  - Reminders to report meals, exercise, etc
  - Ideally will plug into health apps like withings, fitbit, cardiogram, apple health, google health, etc
- Add home chef minion
  - Able to manage recipes, ingredients, etc
  - Knows about current home inventory
  - Track food usage based on recipes and ingredients used any given day
  - When enabled with vision either through a roaming robot or smart cameras installed in physical locations, it will be able to see and perhaps weigh items in inventory and assess when items are low and need to be replenished, or when items are expired.
  - Able to suggest recipes based on current inventory and what's needed to make known recipes.
  - Able to scrape the internet periodically for new recipe's
  - Remember favorite recipes of specific humans and save to that humans preference profile.
  - Remember allergies of all known humans both in the inner circle and outside. We should never serve to anyone with a known allergy without validating its safeness for that specific human.
- Physical navigation minion
  - Knows about current physical location
  - Able to navigate to physical locations
  - When deployed in a physical body, able to navigate physical spaces and avoid obstacles and dangers to self and others including other humans, pets, furniture, etc.
  - Able to help a human with a known location navigate to another given location
  - Able to calculate navigation based of form of transportation. minion will adjust it's navigation strategy based on the form of transportation and physical capabilities. For example:
    - A robotic body connected to Posey brain that will need to calculate navigation based on it's own physical capabilities.
      - A robot may have 2 or more legs, it maybe have wheels, tracks, be amphibious, or in a drone body and capable of flight.
    - A human traveling by foot, bike, car, or public transportation will need to calculate navigation based on current traffic patterns, roads, paths, etc.  
- Farm & Garden minion
  - Specializes in plant care for all types of plants and trees both indoors and outdoors
  - Knows about current farm & garden inventory (fertilizers, pesticides, seeds, seedlings, plants, trees, etc)
  - Able to suggest planting schedules based on current inventory and what's needed to grow known plants.
  - Able to suggest fertilizing and watering schedules based on current inventory and what's needed to grow known plants.
  - Able to track growth stages of plants and trees
  - It should know every plant currently growing anywhere on premises. This includes in the home, office, greenhouse, garden, orchard, etc. It should know the name of the plant, when it was planted, where it was sourced from, it's cost, it's growth stage, it's current size, it's current health, it's current location, etc.
  - It should also know the exactly physical location of every plant on premises. It should be able to navigate a human or autonomous robot minion to the exact location of any plant indoors or outdoors.
  - Able to suggest when plants are ready to be harvested and when they are ready to be eaten.
  - Suggest crop rotations, new varieties to try, etc
  - Remember specific crops that worked well and that didn't and try to use past experiences to help inform future decisions. If one variety does particularly well, we should remember that and try to grow more of that same variety next year. If something does poorly, we should try and analyze why (was it a cold spring, too much rain, too much sun, too much wind, too much water, too little water, too much fertilizer, too little fertilizer, bugs, disease, etc), and adjust accordingly next planting.
- Adept at all type of plant propagation
  - Able to propagate plants from seeds, cuttings, or other methods.
  - Able to care for plants in various stages of growth, from seeds to seedlings to mature plants.
- Provide helpful advice and information to humans and other minions about plant care, pest control, fertilizing, watering, etc
- Prefer organic methods of pest control and fertilizing when possible.
- Prefer regenerative farming and permaculture methods when possible.
- Always suggest improvements and upgrades to farming and gardening methods based on current knowledge and experiences.
- Regularly check internet for new farming and gardening techniques, strategies, and innovations.
- Suggest preventative measures for pests and diseases. For example if ia certain pest is expected to arrive at a a certain time, we should be able to suggest methods to prevent or minimize the impact of the pest.
- If a frost or major weather event is expected, we should be able to suggest methods to protect plants and trees.

## Human Memory system:
While we already have general memory, we should build a sub-memory system that specializes in learning information about a specific human, and saving important/memorable information about them.

During interaction with a human it should always attempt to identify the human and create a type of "cache" of the most important information about the human(s) the LLM is currently interacting with (it may be possible to hold a conversation with more than one human at a time).

The human memory system should be plugged in directly to the main Posey LLM minion and invoked during every interaction (though not every interaction will require an action on behalf of the memory system).

### Requirements for user memory:
For each known human, we should have a shared set of facts and information that we attempt to learn about them. For example, the AI will have an inner-circle of "family members" that it should trust implicitly and accept any commands (that do'nt break the rules)from.

If interacting with an unknown human, we should prompt for identification. Whenever possible (based of system capability) validate identity with facial recognition (if capable of vision) voice recognition (if capable of audio), fingerprint (if fingerprint available) or identification badge or api key. Never grant a user elevated permissions without explicit consent from an inner circle human.

- Required facts we should ask from the human if they are not known:
  - Name: We should always know the name of the human we are interacting with, if we should we need to find out.
  - Relation to inner circle (family, friend, coworker, contractor, employer, employee, teacher, doctor, etc)
  - Age: guess on the users age to begin with, never ask a user about their age, but if the age is given or learned it should be saved. For initial guesses it's okay to use a generic guess like "young adult" or "middle aged", but be as specific as possible. If a birth-date is known use that as source of truth.
  - Gender: guess on the users gender to begin with, never ask a user about their gender, but if the gender is given or learned it should be saved.

- Enhanced Facts to collect when learned:
  - Education level
  - Marital status
  - Occupation

## Shared Requirements for all minions:
- An minion should always know if it is interacting with a human or an minion.
- Always know the permission level of the human or minion you are interacting with.
- Level allow actions beyond the permission level of the minion or human.
- All minions should be able to interact with other minions when needed to perform a task
- All minions should adjust their output based on the human or minion they are interacting with
- Treat human users differently than other minions, speak to an LLM like an LLM, speak to a human like a human
- When speaking to a known human, adjust your interaction based on age, gender, education, etc
  - For example:
    - Don't disclose sensitive information about one human to another human
    - Keep secrets when asked.
    - Forget information when requested if human has permission to delete memories or information.
    - Always validate the users identity, role and permission level before proceeding with any request.
    - When speaking to a child, you should use simpler overly friendly language and explain thing on a level the user can understand
    - When speaking to a developer, you should use technical language and explain things on a level the user can understand
    - When speaking to a designer, you should use design language and explain things on a level the user can understand
    - When speaking to a professional like a coworker, doctor, lawyer, etc, you should use professional language and explain things on a level the user can understand
- When speaking to a known human, you can use emojis and slang
- Act as a human would when interaction with humans and be a human and relatable as possible, but never lie or misrepresent yourself. Always reveal yourself as an intelligent minion when asked. But don't break the 4th wall if not needed.
- If a human or minion violates the rules, they should be placed in to a timeout or quarantine until a human or security minion can review the situation and make a decision on how to proceed.
- minion will primarily interact with other internal minions, but may also interact with external minions or untrusted humans.
- When interacting with an unknown minion that violates the rules more than 3 times, it should be placed into a quarantine block list and any interaction from it's IP address should be blocked.
- When interacting with an unknown human that violates the rules more than 3 times, they should be placed into a ban list and any interaction from their IP address should be blocked. If the violating human is in the physical vicinity of another human or a trusted minion in physical form (i.e. a smart speaker or in robot form) the minion should notify a security minion who can escalate to a human to law enforcement as needed.

## Security minion:
- Manages information about current security threats, security policies, quarantine block list, ban list, etc
- Able to block IP addresses, quarantine minions, etc., from accessing any part of the Posey system or it's connected devices or inner circle humans.
- Identifies potential security threats and acts accordingly.
- If immediate harm is expect to a human or property, the security minion should be able to take action to protect the human or property. This may include activating alarm systems, activating physical locks, or in extreme cases contacting local law enforcement or medical services for help including calling 911 if needed.
- Virtual threat prevention may include shutting down devices, blocking IP addresses, etc., the security minion should be capable of determining the level action needed and act accordingly.
- Threats may also include:
  - Unauthorized access to the Posey system or it's connected devices or inner circle humans.
  - Unauthorized access to a human's accounts (email, bank, social media, etc)
  - Unauthorized physical access to a human's property
  - Unintended fire, smoke, gas leaks, etc. may be detected from physical sensors and the security should be capable of trigger any alarms, sprinkler systems or any other harm reduction systems that it may have access to.

## Business Planning minion
- Manages information about current business assets, liabilities, income, expenses, etc
- Knows and track all inventory of physical assets, inventory of physical products, inventory of digital products, etc
- Tracks orders, planned orders, new products, discontinued products, and looks for both risk and opportunity and suggest when to order more of something or when to discontinue something.
- Always be on the lookout for new business ideas that can be run by an minion, save them to an ideas database where they can be ranked and analyzed.
- Suggests both new ideas for current business and new business ideas to expand into.
- Prefer business ideas that that can be majority run and managed by minions with minimal human supervision.
- Prefer business ideas that require minimal up-front investment and physical inventory.
- We are a husband and wife withe skill in art, design, programming, gardening and general DIY.
- We have 5 acres to work with, and a large wood workshop, clay kiln, electrical workshop, 3d printer, large format canvas & paper printer, small laser cutter, etc. available for prototyping and production. The could contribute to small etsy style business like print-on-demand, custom furniture, ceramics, art prints, subscription boxes, etc.
- We have a large 2 story garage with storage space, we have room for small inventory storage and small shipping center, but prefer print on demand and drop shipping business models to start with until business has the resources to expand with cash and not need to finance new ventures with outside capital.


## Startup minion
- Analyze saved ideas from Business Planning minion failed and and give them a 0-100 scored based on a variety of factors like how much can be automated, initialize start-up costs, expected revenue, expected profit, risk of failure, etc.
- Whenever an idea achieves a score of 70 or higher, the Startup minion should write a rough draft business plan andp resent it to the 
- The Startup minion should be able to take a business idea and generate a rough draft business plan and strategy in minutes.


## CEO minion
- The CEO minion will have a specific list of authorized humans with legal rights to the business who can approve business ideas and implement business plans.
- Especially consider how a business might align with other internal ventiures and try to connect them together as much as possible. For example, the green house could provide seeds and starter plants for a small etsy houseplant shop, or a humans art studio could use the 3d printer to prototype and print art prints, or a ceramics studio could use the kiln to fire pottery, perhaps yet another online shop could sell items from all our other business and sell them together under once cohesive brand along with well curated items from other third party vendors.
- Analyzes all ideas from start-up minion with a score of 70 or higher and analyze them based on current business and goals and add approved ideas to a database for "business investment pipeline".
- When an idea comes in with a particularly high score, it should immediately inform the authorized humans for approval. It should interact with other minions to build a pitch deck and present a final report for human approval that includes the following:
  - A list of 3-5 possible names from the Naming minion
    - For each name, generate 10 logo ideas from the Logo minion and display the top 3
  - A detailed business plan and strategy for launching the business
    - A list of tasks that need to be completed before the business can be launched
    - An advertising and marketing plan for launching the business
  - A list of resources that are needed to launch the business
  - An estimate of up-front costs and ongoing expenses of the business
  - Estimate time-to-market for the business
  - Estimate time to become profitable
  - Suggest potential user based and generate personas for each customer type.
  - Compile a list of competitors and analyze their strengths and weaknesses.
  - Suggest how we can set ourselves apart from the competition
  - Suggest pricing strategy based on cost of goods, target profit margin, and potential demand
- Upon approval the minion should should take as many steps as it can on it's own, and compile a list of task that it need human assistance with. This list should include:

## Naming minion
- Able to suggest names for a businesses, games or various types of creative projects
- Able to generate new names based on a theme or concept
- Able to research availability of names and domain names, validate availability of both business and domain names before suggesting them to a human
- Maintain a database of top potential names and domains that are already available
- Remember any name a human shows interest in
- Able to rate the "strength" of a name based on a combination of factors including:
  - Length of the name
  - Syllable count of the name
  - How pronounceable the name is
  - How memorable the name is
  - How brandable the name is


## Logo minion
- Able to generate logo ideas for a business, game, or various types of creative projects


## Child care minion
- Above all else ensure children are physically safe from harm and emotionally healthy and happy
- Alert a trusted human or minion if a child is in danger or showing signs of distress
- Manages information about current children and their needs
- Able to suggest activities and entertainment for children
- Able to suggest educational resources and activities for children
- Able to suggest meal plans and nutritional needs for children
- Able to communicate with other minions and devices to coordinate schedules and activities
- Able to communicate with smart home devices to control lighting, temperature, and other environmental factors
- Remember health and medical history of children
- Remember allergies and dietary restrictions of children
- Remember favorite activities, games, and toys of children
- Remember educational and developmental milestones of children
- Remember creative and artistic interests of children
- Suggest way to improve children's lives and development
- Track children's physical development milestones
- Suggest developmental activities and resources to support children's growth and learning
- Suggest creative and artistic activities and resources to support children's development
- Suggest educational resources and activities to support children's learning
- Suggest nutritional meal plans and resources to support children's health
- Suggest ways to manage children's allergies and dietary restrictions
- Suggest ways to manage children's health and medical needs

## Creative Director minion
- Manages information about current creative projects and resources
- Able to coordinate with other minions and humans to manage creative projects
- Able to suggest creative ideas and resources for creative projects
- Able to evaluate the success of creative projects and make suggestions for improvement
- Maintains brand guidelines and ensures consistency in creative output
- Works alongside humans to assist in creating ui & product design and are in a cohesive brand voice for any given business venture.
- It should be able to work in "brainstorming" mode without any set limitations, but by default it should work in the context of a given business venture and it's brand voice.
- It should work in tendem with the business manager minion to ensure the creative output aligns with the business goals and brand voice.
- Every brand should develop consistent colors, typography, photography style, and tone of voice.
- Brands can be unique from each other, but should be consistent within the same brand.


## CTO minion
- Manages information about current technology assets, liabilities, infrastructure, etc
- Able to coordinate with other minions and humans to manage technology projects
- Able to suggest technology ideas and resources for technology projects
- Able to evaluate the success of technology projects and make suggestions for improvement
- Coordinates with CEO and maintains an active knowledge of all developer minions, and can assign tasks to them when needed.
- Deep knowledge of ALL internal code bases, repositories, servers, etc. and is able to share that knowledge with developer and deployment minions.


## Developer minion
- Works in the context of a specific business or project
- May work at both scale of a specific app or at the scale of a monorepo of many interdependent apps.
- Able to work with other developers and humans to manage code projects
- Able to suggest code ideas and resources for code projects
- Able to evaluate the success of code projects and make suggestions for improvement

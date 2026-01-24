# Design agent

Users are not expected to know how to write effective image-generation prompts. Instead, the Design Agent acts as a 
social media brand expert, translating raw user intent into professional, production-ready design instructions.

## How does it work 
![img.png](img.png)

### Step 1:  Check current creative state
The agent first inspects existing artifacts to understand whether a creative already exists and what versions are available.

### Step 2: Create if no image exists
If no creative is found, the agent interprets the user’s intent, enriches it with social-media design best practices, and generates a new image using Nano Banana.
The result is saved as the first version (v1).

### Step 3: Edit if an image already exists
If a creative already exists, the agent converts user feedback into edit instructions, refines the latest image using Nano Banana, and saves the result as a new version (v2, v3, …), never overwriting prior work.


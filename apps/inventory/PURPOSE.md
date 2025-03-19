# Posey Inventory
Simple, AI powered inventory management solution for home, business, school and more.

Works as a stand-alone application capable of tracking inventory for many use cases. 

## Basic Usage
Keep your home office, garage, kitchen and other spaces organized with a granular cataloging. Our system is both robust and simple allowing you to organize the way you choose. For example:
- Container Storage: Do you have a garage or basement full of boxes and can never remember what's in them? Posey inventory let's you easily track what's inside of any container (we call these "pods"). You can decide how you want to organize each individual container, it can be a brief description:
"Printer paper is various shapes, weights & colors"

It can be a simple list:
- Paint brushes & rollers
- Mineral Oil
- Putty Knives
- Canvas

Or it can even be a pod full of pods, you can nest pods as deeply as you like! For example:
- Work (Pod)
  - Warehouse (Pod)
    - Supplies (Pod)
    - R&D (Pod)
  - Workshop (Pod)
    - Machining Tools (Pod)
      - 1qty Laser Cutter #1 (Item)
      - 1qty CNC (Item)
  - Inventory (Pod)
    - Returns (Pod)
    - Outgoing Orders (Pod)
    - New Merchandise (Pod)
- Home (Pod)
  - Garage (Pod)
  - Kitchen (Pod)
- Garden (Pod)
  - Garden Shed (Pod)
    - Hand Tools (Pod)
      - Text list of 
    - Fertilizer (Pod)
      - 12qty Vermicompost (Item)
    - 1qty Green Shovel (Item)
  - Greenhouse

Every pod and every item will be assigned a unique ID, permalink, & printable labels in various sizes & templates. Labels can printed on a home inkjet printer, thermal label printer or even engraved on a mtel sign, it's up to you. Labels will include a QR code that be easily scanned with a mobile phone or barcode scanner, and will automatically load a Posey Inventory detail screen for the pod or item scanned.

Examples:
- A warehouse worker can scan an item in an inventory box that may be running and quickly see if any more are stored in other pods, or trigger a an automatic request for a "refill" order. This can be configured to either send a simple notification via SMS, email or push notification, or you can hook into the inventory API to allow authorized users to have the system or AI automatically complete purchases.
- A home user can add a "fridge" pod than can track what items they have in the fridge (addition of smart cameras could automate some inverntory management later). When buying groceries a user can scan the barcode of any items them add and have them automatically added, or manually enter items such as home-made foods. Later if you don't remember how old that chicken is, Posey can automatically notify you when it is no longer safe to eat, and should be thrown out.
- A home user has added both a "fridge" pod, and a "pantry" pod and is looking for dinner idead. They can ask posey "what can I make for dinner" and Posey will know to serch its inventory for any items tagged with food and suggest recipes based on available ingredients
- A woodworker can track tools and supplies stored in oqage storage totes in a a garage. They may twelve 30 gallon totes full or various supplies such as wood glue, screws, nails, and 6 shelves full of wood and tools. They should be able to search the UI or ask Posey (is AI is enabled) things like "where is the wood glue"? and it can something "that's in pod 5 on shelf 3" or return a search result list of all glues stored and the physical location
- An inventorgy manager may want to track throusands of pods across multiple locations, in which case they could use optional geotagging to  track physical locations of materials abd goods.


## Posey Integration
Posey Inventory can *optionally* be seamlessly integrated with the broader Posey AI system to make most interactions even simpler than using the UI. For example instead of getting our a device and scanning a QR code and then visiting an inventory page, a user could just ask a voice-enabled posey device "what's in pod 764?" or "I'm using a paintbrush from Pod 12, can you reduce the inventory by one?", or "we're running low on X can you order more?"
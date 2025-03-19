# Posey Inventory Management

A robust but simple inventory management system that allows you to organize and track your items with QR codes.

## Features

- Create and manage hierarchical storage "pods" (containers, bins, shelves, etc.)
- Track individual items within pods
- Generate QR code labels for pods and items
- Search and filter inventory by various attributes
- API for integration with other systems
- Configurable database (SQLite or PostgreSQL)
- Responsive web interface

## Getting Started

### Prerequisites

- Node.js 18+ and yarn
- For PostgreSQL option: PostgreSQL server
- For Posey integration: Running Posey AI platform with PostgreSQL

### Installation

1. Clone the repository (if not already in your Posey monorepo)

```bash
git clone https://github.com/yourusername/posey-inventory.git
cd posey-inventory
```

2. Install dependencies

```bash
yarn install
```

3. Set up the database

There are multiple ways to set up the database:

#### Option 1: Interactive Database Setup (Recommended)

Run the setup script to interactively configure your database:

```bash
yarn setup-db
```

This will guide you through selecting:
- SQLite (default, no server required)
- PostgreSQL (configure your own connection)
- Existing Posey database (port 3333)

The script automatically:
- Updates the database configuration
- Generates the Prisma client
- Runs initial migrations

#### Option 2: Manual Configuration

Edit the `.env` file directly to set your database connection:

```
# For SQLite (default)
DATABASE_URL="file:./inventory.db"

# For PostgreSQL
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/inventory?schema=public"

# For Posey Integration
DATABASE_URL="postgresql://postgres:postgres@localhost:3333/inventory?schema=public"
```

Then, you'll need to update the Prisma schema and run the migrations:

1. Open `prisma/schema.prisma` and update the provider:
```prisma
datasource db {
  provider = "sqlite" // or "postgresql"
  url      = env("DATABASE_URL")
}
```

2. Generate Prisma client:
```bash
yarn prisma:generate
```

3. Run migrations:
```bash
yarn prisma:migrate
```

#### Option 3: Web Interface

After starting the application, you can also configure the database through the web interface:

1. Start the application: `yarn dev`
2. Navigate to: `http://localhost:8000/config`
3. Configure your database settings
4. Restart the application for changes to take effect

### Starting the Application

```bash
yarn dev
```

The application will be available at `http://localhost:8000`.

## Usage

### Storage Pods

Storage pods are containers that can hold items or other pods. For example:
- A shelving unit containing multiple bins
- A storage tote containing various items
- A filing cabinet with folders

To create a storage pod:
1. Navigate to "Storage Pods" in the sidebar
2. Click "Add New Pod"
3. Fill in details like title, description, location, color, and size
4. Optionally select a parent pod if this is a sub-container

### Items

Items represent individual objects in your inventory. Each item can:
- Have a quantity (e.g., 5 screwdrivers)
- Belong to a storage pod
- Have properties like color, size, and location

To add an item:
1. Navigate to "Items" in the sidebar
2. Click "Add New Item"
3. Fill in details and select which pod it belongs to (optional)

### QR Code Labels

Each pod and item has a unique QR code that can be printed on labels:
1. Navigate to the pod or item details page
2. Click "Print Label"
3. A 4" x 6" label will be generated for printing

### Searching

The search feature allows you to quickly find pods and items:
1. Navigate to "Search" in the sidebar
2. Enter search terms or filter by attributes like color, size, or location
3. Results will show matching pods and items

## API Documentation

The application exposes a RESTful API for integration with other systems:

### Endpoints

- `/api/inventory/pods` - Manage storage pods
- `/api/inventory/items` - Manage items
- `/api/inventory/search` - Search across pods and items
- `/api/inventory/labels` - Generate QR code labels

Check the API documentation in the code for detailed usage.

## Database Configuration

The application supports multiple database providers:

- **SQLite** (default): Simple file-based database, great for single-user deployments
- **PostgreSQL**: Robust database for multi-user deployments or larger inventories
- **Posey Integration**: Uses the existing Posey AI platform database

Configuration can be done through:
- The interactive setup script (`yarn setup-db`)
- The web interface (`/config`)
- Manually editing the database configuration

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributors

- [Your Name](https://github.com/yourusername)

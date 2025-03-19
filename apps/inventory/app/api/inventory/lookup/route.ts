import { NextRequest, NextResponse } from 'next/server';

// Free UPC databases that could be used:
// - https://www.upcdatabase.com/api.asp (requires registration)
// - https://world.openfoodfacts.org/data (open food database)
// - https://api.upcitemdb.com/ (limited to 100 requests per day in free plan)

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const upc = searchParams.get('upc');

  if (!upc) {
    return NextResponse.json(
      { 
        success: false, 
        message: 'UPC parameter is required' 
      }, 
      { status: 400 }
    );
  }

  try {
    // First try UPC Item DB API (has information on various products)
    const response = await fetch(`https://api.upcitemdb.com/prod/trial/lookup?upc=${upc}`, {
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'user_key': process.env.UPC_ITEMDB_API_KEY || '', // Optional API key
      }
    });

    const data = await response.json();

    // Check if we got a valid response with item information
    if (data.items && data.items.length > 0) {
      const item = data.items[0];
      return NextResponse.json({
        success: true,
        data: {
          title: item.title,
          description: item.description || '',
          brand: item.brand,
          category: item.category,
          upc: item.upc,
          source: 'upcitemdb',
          originalData: item
        }
      });
    }

    // Try Open Food Facts as a fallback (mostly for food products)
    const openFoodResponse = await fetch(`https://world.openfoodfacts.org/api/v0/product/${upc}.json`);
    const openFoodData = await openFoodResponse.json();

    // Check if we got valid data from Open Food Facts
    if (openFoodData.status === 1 && openFoodData.product) {
      const product = openFoodData.product;
      return NextResponse.json({
        success: true,
        data: {
          title: product.product_name || 'Unknown Product',
          description: product.ingredients_text || '',
          brand: product.brands || '',
          category: product.categories || '',
          upc: product.code,
          source: 'openfoodfacts',
          originalData: product
        }
      });
    }

    // If nothing found in both APIs
    return NextResponse.json({
      success: false,
      message: 'Product not found',
      upc
    });

  } catch (error) {
    console.error('Error looking up UPC:', error);
    return NextResponse.json(
      { 
        success: false, 
        message: 'Error looking up UPC', 
        error: error instanceof Error ? error.message : String(error)
      }, 
      { status: 500 }
    );
  }
} 
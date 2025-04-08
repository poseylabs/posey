import { NextRequest, NextResponse } from 'next/server';
import { withAuth, ensureUser } from '@/lib/auth';
import { prisma } from '@/lib/db/prisma';

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  return withAuth(request, async (req, user) => {
    try {
      // Await params here to get the id
      const { id: podId } = await params;

      // Ensure user exists
      const dbUser = await ensureUser(prisma, user);
      if (!dbUser) {
        return new NextResponse(JSON.stringify({ error: 'User not found' }), {
          status: 404,
          headers: { 'Content-Type': 'application/json' }
        });
      }

      // Get pod data from request
      const podData = await req.json();
      // Destructure podData carefully, ensuring 'id' from podData doesn't conflict with podId from params
      const { title, contents, id: podDataId, width, height } = podData;

      // Use podId from the route parameters for validation and URL generation
      if (!title || !podDataId) { // Still check if ID is present in the body for label content
        return new NextResponse(JSON.stringify({ error: 'Missing required pod data (title, id) in request body' }), {
          status: 400,
          headers: { 'Content-Type': 'application/json' }
        });
      }

       // Verify the pod belongs to this user using podId from the route
      const pod = await prisma.storagePod.findUnique({
        where: {
          id: podId, // Use podId from route params
          userId: dbUser.id
        }
      });

      if (!pod) {
        return new NextResponse(JSON.stringify({ error: 'Pod not found or not owned by user' }), {
          status: 404,
          headers: { 'Content-Type': 'application/json' }
        });
      }

      // Use provided dimensions or default to 4x6 inches (in mm)
      const labelWidth = width || 152.4; // 6 inches in mm
      const labelHeight = height || 101.6; // 4 inches in mm
      const isSmallLabel = labelWidth < 130; // Check if it's the smaller label size
      
      // Convert mm to pixels at 96 DPI
      const pxWidth = Math.round(labelWidth * 3.779528);
      const pxHeight = Math.round(labelHeight * 3.779528);
      
      // Improve margin to ensure nothing gets cut off during printing
      const margin = Math.round(pxWidth * 0.05); // 5% of width as margin
      
      // Font sizes and spacing based on label size
      const titleSize = isSmallLabel ? 16 : 24;
      const contentSize = isSmallLabel ? 12 : 14;
      const contentLabelSize = isSmallLabel ? 13 : 16;
      
      // Calculate QR code sizes based on label dimensions
      let qrSize;
      if (isSmallLabel) {
        // For 2x4 labels: QR code takes up full height (minus margins)
        qrSize = pxHeight - (margin * 2);
      } else {
        // For 4x6 labels: Make QR code larger - around 60% of the height
        qrSize = Math.round(pxHeight * 0.6);
      }
      
      // Format text with proper wrapping
      const formatTextForSvg = (text: string, maxCharsPerLine: number, maxLines: number): string[] => {
        if (!text) return [];
        
        // Split text into words
        const words = text.split(' ');
        let currentLine = '';
        const lines: string[] = [];
        
        // Create lines that fit within width
        for (const word of words) {
          if ((currentLine + ' ' + word).length <= maxCharsPerLine) {
            currentLine += (currentLine ? ' ' : '') + word;
          } else {
            lines.push(currentLine);
            currentLine = word;
            
            // Check if we've reached max lines
            if (lines.length >= maxLines - 1) {
              break;
            }
          }
        }
        
        // Add the last line
        if (currentLine) {
          lines.push(currentLine);
        }
        
        // If we've hit the max lines and there are more words, add ellipsis
        if (lines.length >= maxLines && words.length > lines.join(' ').split(' ').length) {
          let lastLine = lines[lines.length - 1];
          if (lastLine.length > maxCharsPerLine - 3) {
            lastLine = lastLine.substring(0, maxCharsPerLine - 3) + '...';
          } else {
            lastLine += '...';
          }
          lines[lines.length - 1] = lastLine;
        }
        
        return lines;
      };
      
      // Calculate text wrapping based on label size
      const maxCharsPerLine = isSmallLabel ? 25 : 40;
      const maxLines = isSmallLabel ? 3 : 5;
      const contentLines = contents ? formatTextForSvg(contents, maxCharsPerLine, maxLines) : [];
      
      // Generate QR code URL using podId from route params
      const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=${qrSize}x${qrSize}&data=${encodeURIComponent(`${process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:8000'}/pods/${podId}`)}`;
      
      // Create SVG with improved layouts
      let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${pxWidth}" height="${pxHeight}" viewBox="0 0 ${pxWidth} ${pxHeight}">
        <rect width="100%" height="100%" fill="white"/>`;
      
      if (isSmallLabel) {
        // IMPROVED 2x4 LAYOUT - QR code on left at full height, text on right
        svg += `
        <!-- QR Code filling left side -->
        <image x="${margin}" y="${margin}" width="${qrSize}" height="${qrSize}" href="${qrCodeUrl}"/>
        
        <!-- Title on right side at top -->
        <text x="${margin + qrSize + margin}" y="${margin + titleSize}" 
              font-family="Arial" font-size="${titleSize}" font-weight="bold">${escapeXml(title)}</text>
        
        <!-- Contents section below title on right side -->
        ${contents ? `
        <text x="${margin + qrSize + margin}" y="${margin + titleSize + 24}" 
              font-family="Arial" font-size="${contentLabelSize}" font-weight="bold">Contents:</text>
        ${contentLines.map((line, index) => 
          `<text x="${margin + qrSize + margin}" 
                 y="${margin + titleSize + 24 + (contentSize + 4) * (index + 1)}" 
                 font-family="Arial" font-size="${contentSize}">${escapeXml(line)}</text>`
        ).join('')}
        ` : ''}
        
        <!-- ID at the bottom right -->
        <text x="${margin + qrSize + margin}" y="${pxHeight - margin}" 
              font-family="Arial" font-size="8" fill="#666">ID: ${escapeXml(podDataId)}</text>`;
      } else {
        // IMPROVED 4x6 LAYOUT - Title at top, QR code on left, contents on right
        svg += `
        <!-- Title at the top centered -->
        <text x="${pxWidth / 2}" y="${margin + titleSize}" 
              font-family="Arial" font-size="${titleSize}" font-weight="bold" 
              text-anchor="middle">${escapeXml(title)}</text>
        
        <!-- QR Code larger on left side, positioned below title -->
        <image x="${margin}" y="${margin + titleSize + margin}" 
               width="${qrSize}" height="${qrSize}" 
               href="${qrCodeUrl}"/>
        
        <!-- Contents section to the right of QR code -->
        ${contents ? `
        <text x="${margin + qrSize + margin}" y="${margin + titleSize + margin + contentLabelSize + 10}" 
              font-family="Arial" font-size="${contentLabelSize}" font-weight="bold">Contents:</text>
        ${contentLines.map((line, index) => 
          `<text x="${margin + qrSize + margin}" 
                 y="${margin + titleSize + margin + contentLabelSize + 10 + (contentSize + 6) * (index + 1)}" 
                 font-family="Arial" font-size="${contentSize}">${escapeXml(line)}</text>`
        ).join('')}
        ` : ''}
        
        <!-- ID at the bottom left under the QR code -->
        <text x="${margin}" y="${pxHeight - margin}" 
              font-family="Arial" font-size="10" fill="#666">ID: ${escapeXml(podDataId)}</text>`;
      }
      
      svg += `</svg>`;
      
      // Return SVG
      return new NextResponse(svg, {
        headers: {
          'Content-Type': 'image/svg+xml',
          'Content-Disposition': `inline; filename="${title.replace(/\s+/g, '-')}-label.svg"`,
        },
      });
    } catch (error) {
      console.error('Error generating SVG label:', error);
      return new NextResponse(JSON.stringify({ error: 'Failed to generate label' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  });
}

// Helper function to escape XML special characters
function escapeXml(unsafe: string): string {
  return unsafe.replace(/[<>&'"]/g, c => {
    switch (c) {
      case '<': return '&lt;';
      case '>': return '&gt;';
      case '&': return '&amp;';
      case '\'': return '&apos;';
      case '"': return '&quot;';
      default: return c;
    }
  });
} 
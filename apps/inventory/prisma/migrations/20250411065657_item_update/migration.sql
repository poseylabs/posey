-- AlterTable
ALTER TABLE "Item" ADD COLUMN     "metadata" JSONB,
ADD COLUMN     "upc" TEXT;

-- CreateIndex
CREATE INDEX "Item_upc_idx" ON "Item"("upc");

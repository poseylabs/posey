import { ContentWrapper } from "../layout/content-wrapper";
import { Loading } from "./loading";

export function PageLoading({
  size = 'lg',
  variant = 'infinity'
}:
{
  size?: 'sm' | 'md' | 'lg',
  variant?: string
}) {

  return (
    <ContentWrapper>
      <div className="flex justify-center items-center h-screen w-screen">
        <Loading size={size} variant={variant} />
      </div>
    </ContentWrapper>
  );
}

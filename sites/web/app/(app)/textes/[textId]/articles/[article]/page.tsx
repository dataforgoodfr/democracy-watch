import { ArticleScreen } from "@democracy-watch/screens";

const Page = async ({ params, searchParams }: PageProps<"/textes/[textId]/articles/[article]">) => {
  const { textId, article } = await params;
  return (
    <ArticleScreen
      textId={textId}
      articleNumber={decodeURIComponent(article)}
      params={await searchParams}
    />
  );
};

export default Page;

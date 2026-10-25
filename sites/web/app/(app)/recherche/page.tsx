import { SearchScreen } from "@democracy-watch/screens";

export const metadata = { title: "Recherche" };

const Page = async ({ searchParams }: PageProps<"/recherche">) => (
  <SearchScreen params={await searchParams} />
);

export default Page;

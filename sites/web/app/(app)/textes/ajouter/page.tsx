import { AddTextsScreen } from "@democracy-watch/screens";

export const metadata = { title: "Ajouter des textes à l'étude" };

const Page = async ({ searchParams }: PageProps<"/textes/ajouter">) => (
  <AddTextsScreen params={await searchParams} />
);

export default Page;

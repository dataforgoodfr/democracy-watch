import { LoginScreen } from "@democracy-watch/screens";

export const metadata = { title: "Connexion" };

const Page = async ({ searchParams }: PageProps<"/connexion">) => (
  <LoginScreen params={await searchParams} />
);

export default Page;

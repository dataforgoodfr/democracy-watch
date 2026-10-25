import { FollowedAmendmentsScreen } from "@democracy-watch/screens";

export const metadata = { title: "Mes amendements suivis" };

const Page = async ({ searchParams }: PageProps<"/amendements">) => (
  <FollowedAmendmentsScreen params={await searchParams} />
);

export default Page;

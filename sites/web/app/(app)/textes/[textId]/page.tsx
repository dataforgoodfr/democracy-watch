import { TextScreen } from "@democracy-watch/screens";

const Page = async ({ params }: PageProps<"/textes/[textId]">) => (
  <TextScreen textId={(await params).textId} />
);

export default Page;

import { PromptEditorPage } from "@/components/ai/prompt-editor-page";

export const metadata = { title: "Prompt Editor" };

type PageProps = {
  params: Promise<{ promptId: string }>;
};

export default async function Page({ params }: PageProps) {
  const { promptId } = await params;
  return <PromptEditorPage promptId={promptId} />;
}

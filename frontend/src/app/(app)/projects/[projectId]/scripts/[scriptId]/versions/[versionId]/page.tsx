import { ScriptVersionPage } from "@/components/scripts/script-version-page";

export const metadata = { title: "Script Version" };

type PageProps = {
  params: Promise<{
    projectId: string;
    scriptId: string;
    versionId: string;
  }>;
};

export default async function Page({ params }: PageProps) {
  const { projectId, scriptId, versionId } = await params;
  return (
    <ScriptVersionPage
      projectId={projectId}
      scriptId={scriptId}
      versionId={versionId}
    />
  );
}

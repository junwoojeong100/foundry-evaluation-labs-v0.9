async (page) => {
  page.__stopMediaRecording = async () => {
    const recording = page.__activeRecording;
    if (!recording) throw new Error("No active recording.");
    await recording.page.waitForTimeout(1200);
    const path = await recording.page.video().path();
    const ended = Date.now();
    await recording.context.close();
    const result = {
      id: recording.id, path,
      started_at_ms: recording.started_at_ms,
      ready_offset_ms: recording.ready_offset_ms,
      action_end_offset_ms: recording.action_end_offset_ms ?? ended - recording.started_at_ms,
      ended_at_ms: ended,
    };
    const response = await page.request.post(page.__mediaBaseUrl + "/recording", {data: result});
    if (!response.ok()) throw new Error("Could not persist the capture metadata.");
    page.__activeRecording = null;
    return result;
  };
  return page.__stopMediaRecording();
}

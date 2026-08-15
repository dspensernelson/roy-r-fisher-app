A row on the job worklist — one thing to do, and why it matters.

```jsx
<TaskRow next icon="image" name="Caption the photos and build the photo pages"
  why="Subject Photographs is the only section that builds so far. 18 photos are in the folder."
  chip="Open" onClick={openPhotos} />
<TaskRow tone="done" name="Engagement letter, deed and assessment notice are in" why="Subject Information · 6 files" />
```

In the proposal the `why` names the sections waiting on the task and the folder it belongs in — that is what makes it a plan rather than a list of gaps. Note that it assumes the app can map inputs to sections; if it cannot, the row still works with the second line omitted.

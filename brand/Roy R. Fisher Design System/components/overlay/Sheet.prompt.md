The app's only modal — a question asked inside the action that raised it.

```jsx
<Sheet title="How should the captions read?" sub="Your own photos, written both ways."
  onClose={close}
  foot={<><p className="rrf-sheet__keep">Captions you have already typed are never changed.</p>
    <Button onClick={run}>Use this style</Button><LinkButton onClick={close}>Cancel</LinkButton></>}>
  <PagePreview … />
</Sheet>
```

In this app it is reserved for a question raised by an action — not for settings, confirmations of harmless actions, or announcements.

The loading state — an indeterminate sweep plus what is happening.

```jsx
{busy && <Working label={busy} />}
```

Sits under the action that started it (`ScreenHead below`), not over the content. No spinners, no skeletons.

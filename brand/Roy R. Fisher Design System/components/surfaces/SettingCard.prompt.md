A settings screen is a stack of these — one card per thing you can set.

```jsx
<SettingCard title="Writing captions and reading letters" lamp={<Lamp state="off" />}
  fine="Your key is kept in a file in your own user folder…">
  <p className="rrf-settingcard__body">Two things need a key…</p>
</SettingCard>
```

Body paragraphs use `.rrf-settingcard__body`; the action row uses `.rrf-actionrow`.

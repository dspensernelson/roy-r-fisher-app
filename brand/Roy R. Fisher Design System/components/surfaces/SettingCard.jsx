import React from "react";

/* One card per thing you can set, with the state said in a word. Everything
   about the setting lives inside this card — including the field that changes
   it, which appears only when it is being asked for. */
export function SettingCard({ title, lamp, children, fine }) {
  return (
    <div className="rrf-settingcard">
      <div className="rrf-settingcard__head">
        <h2>{title}</h2>
        {lamp}
      </div>
      {children}
      {fine ? <p className="rrf-settingcard__fine">{fine}</p> : null}
    </div>
  );
}

interface PageHeaderV2Props {
  kicker: string;
  title: string;
  subtitle?: string;
  rightSlot?: React.ReactNode;
}

export function PageHeaderV2({ kicker, title, subtitle, rightSlot }: PageHeaderV2Props) {
  return (
    <header className="v2-page-header">
      <div>
        <p className="v2-page-kicker">{kicker}</p>
        <h1 className="v2-page-title">{title}</h1>
        {subtitle ? <p className="v2-page-subtitle">{subtitle}</p> : null}
      </div>
      {rightSlot ? <div className="shrink-0">{rightSlot}</div> : null}
    </header>
  );
}

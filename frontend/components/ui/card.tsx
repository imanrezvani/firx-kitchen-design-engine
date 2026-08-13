import { cn } from "@/lib/utils";

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-xl border border-border bg-card shadow-sm", className)}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex items-center justify-between border-b border-border px-5 py-4", className)} {...props} />;
}

export function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn("text-base font-bold", className)} {...props} />;
}

export function CardBody({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-5", className)} {...props} />;
}

export function Badge({ className, color = "gray", ...props }: React.HTMLAttributes<HTMLSpanElement> & { color?: string }) {
  const colors: Record<string, string> = {
    gray: "bg-muted/60 text-foreground",
    green: "bg-success/15 text-success",
    amber: "bg-warning/15 text-warning",
    red: "bg-danger/15 text-danger",
    blue: "bg-blue-500/15 text-blue-700",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        colors[color] || colors.gray,
        className,
      )}
      {...props}
    />
  );
}

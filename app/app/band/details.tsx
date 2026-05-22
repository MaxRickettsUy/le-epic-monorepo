import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { statusMap } from "@/lib/const";
import { Band } from "@/lib/types";

export const Details = (props: {
  band: Band
}) => (
  <Card className="w-[75vw] h-full">
    <CardHeader>
      <CardTitle>{props.band.name}</CardTitle>
      <CardDescription>Insert City Hardcore</CardDescription>
    </CardHeader>
    <CardContent>
      <p>Card Content</p>
    </CardContent>
    <CardFooter>
      <p>Card Footer</p>
    </CardFooter>
  </Card>
)
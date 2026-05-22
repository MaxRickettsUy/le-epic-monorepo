import { Band } from "@/lib/types";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./ui/card";
import Image from "next/image";
import { faker } from "@faker-js/faker";
import Link from "next/link";
import { Button } from "./ui/button";

export const TopSection = (props: {
  id: number;
  name: string;
}) => {
  console.log(props)

  return (
    <div className="flex flex-col md:flex-row items-center md:items-start gap-[1rem] justify-between border border-red-500">
      <div className="flex flex-col gap-[1rem]">
        <Card>
          <CardHeader>
            <CardTitle>{props.name}</CardTitle>
            <CardDescription>Insert City Hardcore</CardDescription>
          </CardHeader>
          <CardContent>
            {props.name && (
              <div className="relative">
                <Image
                  className="lg:ml-auto xl:ml-auto rounded-sm"
                  alt={props.name}
                  src={faker.image.urlLoremFlickr({ category: 'people' })}
                  width={250}
                  height={250}
                  priority
                />
              </div>
            )}
          </CardContent>
          <CardFooter>
            <div className="flex flex-col gap-1 w-full">
              <Link href={{ pathname: "/edit/band", query: { id: props.id } }}>
                <Button className="w-full">Edit Band</Button>
              </Link>
              <Link href={{ pathname: "/create/release", query: { band_id: props.id } }}>
                <Button className="w-full">Add Release</Button>
              </Link>
            </div>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
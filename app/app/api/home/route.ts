import { Artist } from '@/lib/types';
import { faker } from '@faker-js/faker';

const capitalizeFirstLetter = (value: string) => {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export async function GET(req: Request) {
  const artists: Artist[] = [...new Array(10)].map((_, index) => {
    return {
      name: capitalizeFirstLetter(faker.word.noun(100)),
      status: "active"
    }
  })

  return Response.json({ artists });
}
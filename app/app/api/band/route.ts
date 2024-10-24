import { Album, Band, Member } from '@/lib/types';
import { faker } from '@faker-js/faker';

const capitalizeFirstLetter = (value: string) => {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

interface Data {
  name: string;
}

export async function POST(req: Request) {
  const data: Data = await req.json();

  const members: Member[] =  [
    {
      name: faker.person.fullName(),
      role: "vocals"
    },
    {
      name: faker.person.fullName(),
      role: "guitarist"
    },
    {
      name: faker.person.fullName(),
      role: "drums"
    },
    {
      name: faker.person.fullName(),
      role: "bass"
    }
  ]

  const albums: Album[] = [...new Array(faker.number.int({ min: 1, max: 5}))].map((_, index) => {
    return {
      name: faker.word.words({ count: { min: 1, max: 5 }}),
      bandName: data.name,
      year: faker.number.int({ min: 1982, max: 2024 }),
      label: capitalizeFirstLetter(faker.word.noun(100)) + "Records",
      rating: faker.number.int({ min: 0, max: 100 }),
      reviewCount: faker.number.int({ min: 0, max: 100 }),
      songs: [],
    }
  })

  const band: Band = {
    name: data.name,
    discography: albums.sort((a, b) => a.year - b.year),
    members,
    status: "active"
  }

  return Response.json(band);

}